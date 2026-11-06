"""Compact, permission-filtered projections of explicit native relationships.

These columns extend the existing storage authorization SELECT. They do not
resolve descendant paths, hydrate related objects, or issue additional queries.
"""

from functools import lru_cache

from daylily_tapdb import generic_instance, generic_instance_lineage
from sqlalchemy import DateTime, and_, case, cast, exists, func, literal, or_, select
from sqlalchemy.orm import aliased

from dewey_service.registry_access import direct_record_clause, maintenance_mode, owner_clause, principal
from dewey_service.share_context import share_context_available


def storage_indicator_columns(session):
    return _indicator_expressions(principal(), share_context_available(), maintenance_mode())


@lru_cache(maxsize=64)
def _indicator_expressions(actor, managed_sharing, maintenance):
    """Return visible set membership and active managed-share audience bits.

    Only immutable SQL expression structure is cached, keyed by the complete
    principal, ingress capability and maintenance mode. Rows, permissions, membership, expiry and
    results are read afresh on every request; database time evaluates expiry.

    Share audience is management-only, matching _registry_share_manager. A
    recipient's permission to discover a share is not permission to inspect its
    other recipients or targets. No private IDs or recipient strings escape.
    """
    record = generic_instance
    collection = aliased(generic_instance)
    member = aliased(generic_instance_lineage)
    in_set = exists(
        select(literal(1))
        .select_from(member)
        .join(collection, collection.uid == member.parent_instance_uid)
        .where(
            member.child_instance_uid == record.uid,
            member.relationship_type == "artifact_set_member",
            member.is_deleted.is_(False),
            collection.type == "artifact_set",
            collection.is_deleted.is_(False),
            collection.bstatus != "archived",
            collection.domain_code == record.domain_code,
            collection.issuer_app_code == record.issuer_app_code,
            direct_record_clause(None, collection),
        )
    ).correlate(record)
    if not managed_sharing:
        return in_set, literal(0)

    share, revision, grant = (aliased(generic_instance) for _ in range(3))
    revision_edge, target_edge, grant_edge, grant_target = (
        aliased(generic_instance_lineage) for _ in range(4)
    )
    data, rule = share.json_addl, grant.json_addl
    now = func.now()
    # Exact lsmc.com predicates only. Subdomains, lsmc.bio, other domains,
    # named external recipients and public-with-registration are broader.
    exact_lsmc = or_(
        and_(rule["recipient_type"].astext == "email",
             func.split_part(rule["recipient"].astext, "@", 2) == "lsmc.com"),
        and_(rule["recipient_type"].astext == "domain",
             rule["recipient"].astext == "lsmc.com",
             rule["include_subdomains"].astext == "false"),
    )
    share_bits = (
        select(func.coalesce(func.bit_or(case((exact_lsmc, 4), else_=8)), 0))
        .select_from(target_edge)
        .join(revision, revision.uid == target_edge.parent_instance_uid)
        .join(revision_edge, revision_edge.child_instance_uid == revision.uid)
        .join(share, share.uid == revision_edge.parent_instance_uid)
        .join(grant_edge, grant_edge.parent_instance_uid == share.uid)
        .join(grant, grant.uid == grant_edge.child_instance_uid)
        .join(grant_target, grant_target.parent_instance_uid == grant.uid)
        .where(
            target_edge.child_instance_uid == record.uid,
            target_edge.relationship_type == "share_revision_target",
            revision_edge.relationship_type == "share_revision",
            grant_edge.relationship_type == "share_grant",
            grant_target.relationship_type == "share_grant_target",
            grant_target.child_instance_uid == record.uid,
            *(edge.is_deleted.is_(False) for edge in
              (target_edge, revision_edge, grant_edge, grant_target)),
            revision.type == "share_revision",
            share.type == "share",
            grant.type == "share_grant",
            *(obj.is_deleted.is_(False) for obj in (revision, share, grant)),
            *(obj.domain_code == record.domain_code for obj in (revision, share, grant)),
            *(obj.issuer_app_code == record.issuer_app_code for obj in (revision, share, grant)),
            share.bstatus != "archived",
            data["schema_version"].astext == "3",
            data["status"].astext == "active",
            rule["status"].astext == "active",
            rule["recipient_type"].astext.in_(("email", "domain", "registered")),
            revision.json_addl["policy_revision"].astext == data["policy_revision"].astext,
            rule["policy_revision"].astext == data["policy_revision"].astext,
            or_(data["expires_at"].astext.is_(None),
                cast(data["expires_at"].astext, DateTime(timezone=True)) > now),
            or_(rule["expires_at"].astext.is_(None),
                cast(rule["expires_at"].astext, DateTime(timezone=True)) > now),
            literal(True) if actor.admin else owner_clause(data, actor),
        )
        .correlate(record)
        .scalar_subquery()
    )
    return in_set, share_bits
