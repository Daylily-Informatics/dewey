"""Creator-and-audience lifetime policy and explicit inactive-share revival."""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from dewey_service.registry_access import principal
from dewey_service.services.share_policy import UNSET, expiry, normalized_policy
from dewey_service.tapdb_backend import normalize_instance_payload, utc_now_iso

INTERNAL_DOMAINS = frozenset({'lsmc.com', 'lsmc.bio'})


def lifetime_policy(creator, data):
    email = str(creator.get('email') or '').strip().lower()
    creator_internal = (creator.get('email_verified') is True and creator.get('service') is False
                        and email.count('@') == 1 and email.rpartition('@')[2] in INTERNAL_DOMAINS)
    grants = data.get('grants')
    if grants is None:
        grants = ([{'recipient_type':'email','recipient':e} for e in data.get('allowed_users',[])] +
                  [{'recipient_type':'domain','recipient':d} for d in data.get('allowed_domains',[])])
    if not isinstance(grants,list) or any(not isinstance(g,dict) for g in grants):
        raise ValueError('grants must be a list of explicit recipient predicates')
    recipients_internal = bool(grants) and data.get('audience','recipients') == 'recipients'
    for grant in grants:
        recipient = str(grant.get('recipient') or '').strip().lower()
        kind = grant.get('recipient_type')
        exact = (kind == 'email' and recipient.count('@') == 1 and
                 bool(recipient.partition('@')[0]) and recipient.rpartition('@')[2] in INTERNAL_DOMAINS)
        exact = exact or (kind == 'domain' and recipient in INTERNAL_DOMAINS and
                          grant.get('include_subdomains',False) is False)
        recipients_internal = recipients_internal and exact
    indefinite = bool(creator_internal and recipients_internal)
    return {'version':1,'creator':creator,'creator_internal_verified':bool(creator_internal),
            'audience_internal_exact':bool(recipients_internal),'indefinite_allowed':indefinite,
            'default_lifetime_days':None if indefinite else 14,
            'max_lifetime_days':None if indefinite else 365,
            'rule':'No expiry requires the original verified lsmc.com/lsmc.bio account creator and an entirely exact internal audience. All other shares default to 14 days, maximum 365 days; subdomains and public registration are bounded.'}


def normalize_lifetime(raw, policy, *, now=None):
    now = now or datetime.now(timezone.utc)
    if raw is UNSET:
        days = policy['default_lifetime_days']
        return None if days is None else (now+timedelta(days=days)).isoformat()
    if raw is None:
        if not policy['indefinite_allowed']:
            raise ValueError('No expiry requires a verified original lsmc.com/lsmc.bio creator and an entirely exact internal audience')
        return None
    result = expiry(raw)
    if result <= now:
        raise ValueError('Share expiry must be in the future')
    maximum = policy['max_lifetime_days']
    if maximum is not None and result > now+timedelta(days=maximum):
        raise ValueError('This creator/audience requires a finite expiry within 365 days')
    return result.isoformat()


def validate_activation_generation(context, share_data):
    if context.get('share_activation_generation',0) != share_data.get('activation_generation',0):
        raise HTTPException(410,'Share was revived; reopen a new delivery context from Dewey')


def validate_access_package(query, resolved):
    names=('policy_revision','activation_generation')
    supplied=[query.getlist(k) for k in names]
    if not any(supplied):
        return  # Ordinary canonical URLs remain locators requiring current grants.
    if any(len(values)!=1 for values in supplied):
        raise HTTPException(400,'Access-package revision and activation pins are required together once')
    try:
        revision,generation=(int(values[0]) for values in supplied)
    except (ValueError,TypeError) as exc:
        raise HTTPException(400,'Invalid access-package pins') from exc
    if (revision!=resolved['policy_revision'] or generation!=resolved.get('activation_generation',0)):
        raise HTTPException(410,'Access package is stale; request a new package under the current policy')


class ShareExpiryMixin:
    def _new_share_creator(self):
        actor=principal()
        return {'email':actor.email,'email_verified':bool(actor.email_verified),
                'service':bool(actor.service),'subject':actor.subject,'proof':'current_authenticated_creator'}

    def _share_creator(self, session, share):
        data=normalize_instance_payload(share)
        creator={'email':data['owner_email'],'subject':data['owner_subject'],
                 'email_verified':False,'service':True,'proof':'unknown_original_creator_verification'}
        if type(data.get('creator_email_verified')) is bool and type(data.get('creator_service')) is bool:
            return {**creator,'email_verified':data['creator_email_verified'],
                    'service':data['creator_service'],'proof':'persisted_original_creator'}
        # Old native creation audit is authoritative; never borrow an editor's identity.
        created=[r for r in self._share_related(session,share,relationship='share_event',kind='share_event')
                 if normalize_instance_payload(r).get('event_type')=='created'
                 and normalize_instance_payload(r).get('actor')==data['owner_subject']]
        if len(created)==1:
            event=normalize_instance_payload(created[0])
            creator.update(email_verified=event.get('actor_email_verified') is True,
                           service=event.get('actor_service') is not False,
                           proof='native_created_event',proof_event_euid=created[0].euid)
        return creator

    def _revivable_grants(self, session, share):
        data=normalize_instance_payload(share)
        rows=self._share_grants(session,share)
        revisions=[normalize_instance_payload(g).get('policy_revision',0) for g in rows
                   if normalize_instance_payload(g).get('policy_revision',0)<=data['policy_revision']]
        if not revisions:
            return []
        latest=max(revisions)
        return [g for g in rows if normalize_instance_payload(g).get('policy_revision')==latest
                and normalize_instance_payload(g).get('status')=='active']

    def share_expiry_policy(self):
        if not principal().writable:
            raise HTTPException(403,'Share creation requires write access')
        return lifetime_policy(self._new_share_creator(),{})

    def revive_share(self, euid, *, policy_revision, expires_at, grant_euids, reason,
                     reauthorize_public_registered=False):
        from dewey_service.services.sharing import _grant_policy_payload
        self._require_sharing()
        with self.backend.session_scope(commit=True) as session:
            share=self._canonical_share(session,euid,lock=True)
            if not self._registry_share_manager(session,share):
                raise HTTPException(403,'Share management permission required')
            data=normalize_instance_payload(share)
            if type(policy_revision) is not int or data['policy_revision']!=policy_revision:
                raise HTTPException(409,'Share policy changed; reload before revival')
            if data['status']=='active' and expiry(data['expires_at'])>datetime.now(timezone.utc):
                raise ValueError('Only an inactive or expired share can be explicitly revived')
            if share.bstatus=='archived':
                raise ValueError('Archived share cannot be revived through this action')
            if expires_at is None or expires_at is UNSET:
                raise ValueError('Revival requires an explicit new finite expiration')
            if not isinstance(reason,str) or not reason.strip():
                raise ValueError('Revival requires a reason and explicit recipient reauthorization')
            if not isinstance(grant_euids,list) or len(grant_euids)!=len(set(grant_euids)):
                raise ValueError('Review distinct existing recipient grant identities')
            members=self._share_members(session,share)
            self._assert_share_delegation(session,members)
            eligible={g.euid:g for g in self._revivable_grants(session,share)
                      if normalize_instance_payload(g)['recipient_type']!='registered'}
            if not set(grant_euids)<=eligible.keys():
                raise ValueError('Only previously active recipients may be reauthorized; revoked grants are excluded')
            public=data['audience']=='public_registered'
            if public and reauthorize_public_registered is not True:
                raise ValueError('Public-with-registration audience requires explicit reauthorization')
            if not public and reauthorize_public_registered:
                raise ValueError('Revival cannot expand a named audience to public registration')
            if not grant_euids and not public:
                raise ValueError('Select at least one existing recipient to reauthorize')
            grants=[]
            for grant_id in grant_euids:
                grant=eligible[grant_id];value=_grant_policy_payload(normalize_instance_payload(grant))
                targets=[t.euid for t in self._grant_targets(session,grant)]
                if not targets or not set(targets)<={m.euid for m in members}:
                    raise ValueError('Revival grant targets differ from the current retained members')
                value.update(target_euids=targets,expires_at=expires_at)
                grants.append(value)
            creator=self._share_creator(session,share)
            scope=lifetime_policy(creator,{**data,'grants':grants})
            deadline=normalize_lifetime(expires_at,scope)
            policy=normalized_policy({**data,'grants':grants},share_expiry=deadline,
                                     member_euids=[m.euid for m in members])
            self._validate_report_selection(policy,members)
            grants=policy.pop('grants');revision=policy_revision+1
            generation=data.get('activation_generation',0)+1
            for grant in self._share_grants(session,share):
                if normalize_instance_payload(grant).get('status')=='active':
                    self.backend.update_instance_json(session,grant,{'status':'superseded'})
            # Retire aliases, invalidate existing preview contexts, and preserve
            # their previous receipt fields. They are never silently reactivated.
            retired=[]
            for alias in self._share_aliases(session,share):
                if alias['status']=='active':
                    row=self._find_share_alias(session,alias['slug'],lock=True)
                    self.backend.update_instance_json(session,row,{'status':'retired','retired_at':utc_now_iso()})
                    retired.append(alias['slug'])
            for row in self._share_related(session,share,relationship='has_storage_operation',kind='storage_operation'):
                operation=normalize_instance_payload(row)
                if operation.get('operation')=='share_notification' and operation.get('status')=='pending':
                    self.backend.update_instance_json(session,row,{'status':'cancelled','completed_at':utc_now_iso(),'last_error':'Share explicitly revived; prior notification intent not resent'})
                if operation.get('operation')=='isolated_report_context' and operation.get('status')!='revoked':
                    self.backend.update_instance_json(session,row,{'status':'revoked','revoked_at':utc_now_iso(),
                                                       'revocation_reason':'share_explicitly_revived'})
            self._write_share_revision(session,share,members,revision,policy={**policy,'expires_at':deadline})
            self._write_grants(session,share,grants,members,revision)
            self.backend.update_instance_json(session,share,{**policy,'status':'active','expires_at':deadline,
                'policy_revision':revision,'activation_generation':generation,'revived_at':utc_now_iso(),
                'creator_email_verified':creator['email_verified'],'creator_service':creator['service']})
            self._event(session,share,event_type='revived',decision='revive',details={
                'reason':reason.strip(),'policy_revision':revision,'previous_policy_revision':policy_revision,
                'previous_status':data['status'],'previous_expires_at':data['expires_at'],
                'reauthorized_grant_euids':grant_euids,'retired_aliases':retired,'activation_generation':generation})
            session.refresh(share)
            # Revival creates no automatic notification intent or dispatch.
            return self._canonical_response(session,share,manager=True)
