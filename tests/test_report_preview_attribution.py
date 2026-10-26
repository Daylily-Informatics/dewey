"""Isolated report requests retain native attribution without an app cookie.

The real routes, lineage lookups, identity binding, share evaluator, TapDB
transaction wrapper and response audits run here. Only database, provider and
object-storage I/O are replaced; unattributed writes retain the production guard.
"""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
from types import SimpleNamespace

import pytest
from daylily_auth_cognito.browser.session import CONFIG_STATE_KEY, SessionPrincipal
from daylily_tapdb import generic_instance, generic_instance_lineage
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import BinaryExpression, BindParameter, False_

from dewey_service.audit import authenticated_user_email_context, current_authenticated_user_email
from dewey_service.registry_access import (
    OPERATION_TEMPLATE,
    POLICY_TEMPLATE,
    Principal,
    current_principal,
    principal_context,
)
from dewey_service.report_preview import attach_report_preview, report_entry_page
from dewey_service.services.share_policy import EVENT_TEMPLATE, GRANT_TEMPLATE
from dewey_service.services.sharing import SharingServiceMixin
from dewey_service.share_context import ManagedShareIngressMiddleware
from dewey_service.share_routing import ShareHostBoundaryMiddleware
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE,
    SHARE_REVISION_TEMPLATE,
    SHARE_TEMPLATE,
    TapDBBackend,
)

ACTOR = Principal(
    subject="viewer-fixture",
    email="viewer@example.test",
    roles=("READ_ONLY",),
    email_verified=True,
    recipient_only=True,
    identity_grant_id="provider-binding-fixture",
    identity_revision=1,
    identity_expires_at="2099-01-01T00:00:00+00:00",
)
HOST = "pv-" + "a" * 32 + ".content.example.test"
FUTURE = "2099-01-01T00:00:00+00:00"


class ReportShell(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.frames, self.scripts = [], []
        self.feed(content.decode())

    def handle_starttag(self, tag, attrs):
        if tag == "iframe":
            self.frames.append(dict(attrs))
        elif tag == "script":
            self.scripts.append(dict(attrs))


def policy_directives(response):
    return {
        parts[0]: set(parts[1:])
        for directive in response.headers["content-security-policy"].split(";")
        if (parts := directive.strip().split())
    }


def _value(expression, instance, lineage):
    if isinstance(expression, BindParameter):
        return expression.value
    if isinstance(expression, False_):
        return False
    if isinstance(expression, BinaryExpression):
        left, right = (
            _value(expression.left, instance, lineage),
            _value(expression.right, instance, lineage),
        )
        if expression.operator in (operators.eq, operators.is_):
            return left == right
        if (
            expression.operator is operators.json_getitem_op
            or getattr(expression.operator, "opstring", None) == "->>"
        ):
            return left.get(right)
        raise AssertionError(f"Unexpected query operation: {expression.operator}")
    row = lineage if expression.table.name == generic_instance_lineage.__table__.name else instance
    return getattr(row, expression.key)


class Query:
    def __init__(self, database, rows):
        self.database, self.rows = database, rows

    def join(self, model, expression):
        assert model is generic_instance_lineage
        self.rows = [
            (row, edge)
            for row, _ in self.rows
            for edge in self.database.lineages
            if _value(expression, row, edge)
        ]
        return self

    def filter(self, *expressions):
        self.rows = [
            (row, edge)
            for row, edge in self.rows
            if all(_value(expression, row, edge) for expression in expressions)
        ]
        return self

    def filter_by(self, **values):
        self.rows = [
            (row, edge)
            for row, edge in self.rows
            if all(getattr(row, key) == value for key, value in values.items())
        ]
        return self

    def with_for_update(self):
        self.database.locks.extend(row.euid for row, _ in self.rows)
        return self

    def limit(self, count):
        self.rows = self.rows[:count]
        return self

    def all(self):
        return [row if row is not None else edge for row, edge in self.rows]

    def first(self):
        return next(iter(self.all()), None)

    def one(self):
        rows = self.all()
        assert len(rows) == 1
        return rows[0]


class Database:
    def __init__(self):
        self.rows, self.lineages, self.transactions, self.locks = [], [], [], []

    def template(self, session, code, *, domain_code):
        assert domain_code == "fixture"
        return SimpleNamespace(uid=code, type=code.split("/")[1])

    def create(self, code, label, **payload):
        now = datetime.now(timezone.utc)
        row = SimpleNamespace(
            uid=len(self.rows) + 1,
            euid=label,
            template_uid=code,
            type=code.split("/")[1],
            domain_code="fixture",
            name=label,
            bstatus="active",
            is_deleted=False,
            polymorphic_discriminator="generic_instance",
            record_revision=1,
            created_dt=now,
            modified_dt=now,
            json_addl={"properties": {}, **deepcopy(payload)},
        )
        self.rows.append(row)
        return row

    def link(self, parent, child, relationship):
        self.lineages.append(
            SimpleNamespace(
                parent_instance_uid=parent.uid,
                child_instance_uid=child.uid,
                relationship_type=relationship,
                is_deleted=False,
            )
        )

    def query(self, model):
        assert model in (generic_instance, generic_instance_lineage)
        return Query(
            self,
            [(row, None) for row in self.rows]
            if model is generic_instance
            else [(None, edge) for edge in self.lineages],
        )

    def connect(self, path):
        database = self

        class Connection:
            @contextmanager
            def session_scope(connection, *, commit):
                # TapDBBackend has already executed its real transaction_attribution.
                attribution = connection.attribution
                if commit:
                    assert attribution.actor_subject == ACTOR.subject
                    assert current_authenticated_user_email() == ACTOR.email
                database.transactions.append((commit, attribution))
                yield SimpleNamespace(
                    query=database.query,
                    get_bind=lambda: None,
                    attribution=attribution,
                    add=database.add,
                    flush=lambda: None,
                )

        return Connection()

    def add(self, edge):
        edge.is_deleted = False
        self.lineages.append(edge)

    def insert(self, *, session, template_code, name, properties, create_children):
        assert session.attribution.actor_subject == ACTOR.subject
        return self.create(template_code, f"persisted-fixture-{len(self.rows) + 1}")

    def update(self, session, selector, changes, *, actor, dry_run, expected_revision):
        assert session.attribution.actor_subject == ACTOR.subject
        row = next(row for row in self.rows if row.euid == selector.euid)
        assert row.record_revision == expected_revision and dry_run is False
        for key, value in changes.items():
            setattr(row, key, deepcopy(value))
        row.record_revision += 1


@pytest.fixture
def preview(monkeypatch):
    database = Database()
    binding = database.create(
        OPERATION_TEMPLATE,
        "persisted-session-fixture",
        operation="browser_session_binding",
        status="active",
        actor=ACTOR.subject,
        principal=asdict(ACTOR),
        generation="generation-fixture",
        expires_at=FUTURE,
    )
    context = database.create(
        OPERATION_TEMPLATE,
        "persisted-context-fixture",
        operation="isolated_report_context",
        status="pending",
        actor=ACTOR.subject,
        context_host=HOST,
        bundle_root="report/",
        report_relative_key="report/multiqc.html",
        object_only=False,
        expires_at=FUTURE,
    )
    share = database.create(
        SHARE_TEMPLATE,
        "persisted-share-fixture",
        schema_version=3,
        status="active",
        policy_revision=1,
        expires_at=None,
        denied_emails=[],
        delivery_modes=["gateway"],
        content_mode="www",
        include_patterns=["**"],
        exclude_patterns=[],
        report_entrypoint="report/multiqc.html",
        report_bundle_root="report/",
    )
    target = database.create(
        ARTIFACT_TEMPLATE,
        "persisted-target-fixture",
        storage_backend="s3",
        storage_kind="prefix",
        bucket="bucket-fixture",
        key="source/",
        location_revision=1,
    )
    grant = database.create(
        GRANT_TEMPLATE,
        "persisted-grant-fixture",
        status="active",
        policy_revision=1,
        expires_at=None,
        recipient_type="registered",
        include_patterns=["**"],
        exclude_patterns=[],
    )
    revision = database.create(
        SHARE_REVISION_TEMPLATE, "persisted-revision-fixture", policy_revision=1
    )
    database.create(
        POLICY_TEMPLATE,
        "persisted-schema-fixture",
        policy_kind="sharing_schema",
        schema_version=3,
        status="verified",
    )
    for parent, child, relationship in (
        (binding, context, "has_report_context"),
        (target, context, "preview_target"),
        (share, context, "has_storage_operation"),
        (share, revision, "share_revision"),
        (revision, target, "share_revision_target"),
        (target, share, "has_share"),
        (share, grant, "share_grant"),
        (grant, target, "share_grant_target"),
    ):
        database.link(parent, child, relationship)
    settings = SimpleNamespace(
        auth_mode="external_broker",
        external_broker_handoff_exchange_url="https://login.example.test/handoff",
        share_application_origin="https://dewey.example.test",
        share_content_host_suffix="content.example.test",
        share_session_generation="generation-fixture",
        cognito_group_role_map={},
        registry_internal_domains={"lsmc.bio"},
        share_trusted_proxy_peer="127.0.0.1",
        share_ingress_assertion_header="X-Dewey-Tailnet-Assertion",
        share_ingress_assertion="private-fixture-" * 3,
        share_public_ingress_assertion_header="X-Dewey-Recipient-Assertion",
        share_public_ingress_assertion="public-fixture-" * 3,
    )
    backend = object.__new__(TapDBBackend)
    backend.settings, backend.config_path, backend.domain_code = (
        settings,
        "/fixture/native-config",
        "fixture",
    )
    backend.connection, backend.observability = SimpleNamespace(app_username="dewey"), None
    backend.templates = SimpleNamespace(get_template=database.template)
    backend.factory = SimpleNamespace(create_instance=database.insert)
    monkeypatch.setattr("dewey_service.tapdb_backend.get_db", database.connect)
    monkeypatch.setattr("dewey_service.tapdb_backend.update_object", database.update)
    monkeypatch.setattr("dewey_service.performance.instrument_engine", lambda engine: None)
    state = SimpleNamespace(
        disabled=False, verify_hook=None, storage_calls=[], bodies=[], signed_in=True
    )

    def verify(settings, **identity):
        assert identity == {"grant_id": ACTOR.identity_grant_id, "revision": 1}
        if state.disabled:
            raise HTTPException(401, "Provider disabled identity")
        if state.verify_hook:
            state.verify_hook()
        return {
            "canonical_user_id": ACTOR.subject,
            "email": ACTOR.email,
            "email_verified": True,
            "grant_id": ACTOR.identity_grant_id,
            "revision": 1,
            "expires_at": FUTURE,
        }

    monkeypatch.setattr("dewey_service.recipient_identity.verify_recipient_binding", verify)

    def stored_object(**kwargs):
        from dewey_service.storage import _STORAGE_AUTHORIZATION

        _STORAGE_AUTHORIZATION.get()(
            kwargs["bucket"], kwargs["key"], action="metadata" if kwargs["head"] else "download"
        )
        state.storage_calls.append(kwargs)
        content = (
            b"<html>report</html>" if kwargs["key"].endswith(".html") else b"body{color:black}"
        )
        result = {
            "ContentLength": len(content),
            "ETag": '"fixture-etag"',
            "VersionId": "fixture-version",
        }
        if not kwargs["head"]:
            result["Body"] = BytesIO(content)
            state.bodies.append(result["Body"])
        return result

    service = SharingServiceMixin()
    service.backend, service.requester_pays_buckets = backend, set()
    service._require_storage = lambda: SimpleNamespace(object_response=stored_object)
    app = FastAPI()
    app.state.settings = settings
    app.state.__dict__[CONFIG_STATE_KEY] = SimpleNamespace(server_instance_id=None)
    session_user = SessionPrincipal(
        user_sub=ACTOR.subject,
        email=ACTOR.email,
        roles=list(ACTOR.roles),
        app_context={"dewey_session_binding_euid": binding.euid},
    )

    class ApplicationIdentity:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            signed_in = (
                dict(scope.get("headers", ())).get(b"host") == b"dewey.example.test"
                and state.signed_in
            )
            scope["session"] = session_user.to_session_dict() if signed_in else {}
            with (
                principal_context(ACTOR if signed_in else None),
                authenticated_user_email_context(ACTOR.email if signed_in else None),
            ):
                await self.app(scope, receive, send)

    attach_report_preview(app, APIRouter(), service)
    app.add_middleware(ApplicationIdentity)
    app.add_middleware(ShareHostBoundaryMiddleware, settings=settings)
    app.add_middleware(ManagedShareIngressMiddleware, settings=settings)
    client = TestClient(
        app,
        base_url="https://" + HOST,
        client=("127.0.0.1", 40000),
        headers={
            settings.share_public_ingress_assertion_header: settings.share_public_ingress_assertion
        },
    )
    with client:
        yield SimpleNamespace(
            client=client,
            app=app,
            database=database,
            context=context,
            binding=binding,
            state=state,
            settings=settings,
            service=service,
            share=share,
        )


def test_isolated_challenge_handoff_and_asset_audits_have_native_viewer_attribution(preview):
    p = preview
    response = p.client.get("/__dewey_preview/challenge")
    assert response.status_code == 200
    assert response.headers["referrer-policy"] == "no-referrer"
    cookie = p.client.cookies.get("__Host-dewey_preview")
    assert cookie and p.context.json_addl["status"] == "challenged"
    assert p.context.json_addl["updated_by_email"] == ACTOR.email
    assert p.database.transactions[0] == (False, None)
    assert p.context.euid in p.database.locks
    assert p.client.get("/__dewey_preview/assets/multiqc.html").status_code == 401
    assert not p.state.storage_calls

    endpoint = f"https://dewey.example.test/api/v2/recipient/shares/{p.share.euid}/preview/{p.context.euid}/handoff"
    p.state.signed_in = False
    assert (
        p.client.post(endpoint, json={"challenge": sha256(cookie.encode()).hexdigest()}).status_code
        == 403
    )
    p.state.signed_in = True
    handoff = p.client.post(endpoint, json={"challenge": sha256(cookie.encode()).hexdigest()})
    assert handoff.status_code == 200
    assert p.client.get("/__dewey_preview/assets/multiqc.html").status_code == 401
    form = {"token": handoff.json()["token"]}
    assert (
        p.client.post("/__dewey_preview/handoff", data=form, headers={"Origin": "null"}).status_code
        == 403
    )
    accepted = p.client.post(
        "/__dewey_preview/handoff",
        data=form,
        headers={"Origin": p.settings.share_application_origin},
        follow_redirects=False,
    )
    assert accepted.status_code == 303
    assert p.context.json_addl["status"] == "active" and p.context.json_addl["handoff_sha256"] == ""
    assert (
        p.client.post(
            "/__dewey_preview/handoff",
            data=form,
            headers={"Origin": p.settings.share_application_origin},
            follow_redirects=False,
        ).status_code
        == 403
    )

    report = p.client.get(accepted.headers["location"])
    assert report.status_code == 200 and report.content == b"<html>report</html>"
    request = Request(
        {"type": "http", "method": "GET", "path": "/fetch/fixture", "headers": [], "app": p.app}
    )
    wrapper = report_entry_page(
        request,
        {"share_euid": p.share.euid, "report_bundle_root": "report/"},
        {"target_euid": "persisted-target-fixture", "relative_key": "report/multiqc.html"},
    )
    shell = ReportShell(wrapper.body)
    assert len(shell.frames) == 1
    iframe_permissions = set(shell.frames[0]["sandbox"].split())
    content_policy = policy_directives(report)
    export_permissions = {"allow-scripts", "allow-same-origin", "allow-forms", "allow-downloads"}
    # Both enforced sandbox layers must permit the submit handler and blob save.
    # Exact permission sets also exclude popup and top-navigation escape tokens.
    assert iframe_permissions == content_policy["sandbox"] == export_permissions
    assert iframe_permissions & content_policy["sandbox"] == export_permissions
    for directive in (
        "default-src",
        "form-action",
        "worker-src",
        "object-src",
        "frame-src",
        "base-uri",
    ):
        assert content_policy[directive] == {"'none'"}
    assert content_policy["connect-src"] == {"'self'"}
    assert content_policy["frame-ancestors"] == {p.settings.share_application_origin}
    assert "blob:" in content_policy["img-src"]
    sidecar = p.client.get("/__dewey_preview/assets/assets/style.css")
    assert sidecar.status_code == 200 and sidecar.headers["content-type"] == "text/css"
    head = p.client.head("/__dewey_preview/assets/assets/style.css")
    assert head.status_code == 200 and not head.content
    assert [call["key"] for call in p.state.storage_calls] == [
        "source/report/multiqc.html",
        "source/report/assets/style.css",
        "source/report/assets/style.css",
    ]
    assert all(body.closed for body in p.state.bodies)
    events = [row.json_addl for row in p.database.rows if row.template_uid == EVENT_TEMPLATE]
    completed = [event for event in events if event["event_type"] == "gateway_response_completed"]
    assert len(completed) == 3 and all(event["actor"] == ACTOR.subject for event in events)
    assert all(event["created_by_email"] == ACTOR.email for event in events)
    assert all(
        attribution.actor_subject == ACTOR.subject
        for commit, attribution in p.database.transactions
        if commit
    )
    p.state.disabled = True
    assert p.client.get("/__dewey_preview/assets/multiqc.html").status_code == 401
    p.state.disabled = False
    p.binding.json_addl["status"] = "revoked"
    assert p.client.get("/__dewey_preview/assets/assets/style.css").status_code == 401
    assert len(p.state.storage_calls) == 3
    assert current_principal() is None and current_authenticated_user_email() is None


@pytest.mark.parametrize("change", ["disabled", "binding_changed", "session_revoked"])
def test_isolated_challenge_rejects_stale_identity_before_mutation(preview, change):
    p = preview
    if change == "disabled":
        p.state.disabled = True
    elif change == "binding_changed":
        p.state.verify_hook = lambda: p.binding.json_addl["principal"].update(identity_revision=2)
    else:
        p.state.verify_hook = lambda: p.binding.json_addl.update(status="revoked")
    response = p.client.get("/__dewey_preview/challenge")
    assert response.status_code == (409 if change == "binding_changed" else 401)
    assert p.context.json_addl["status"] == "pending"
    assert "cookie_sha256" not in p.context.json_addl
    assert not p.state.storage_calls and "set-cookie" not in response.headers


def test_report_wrapper_preserves_exact_origin_for_native_handoff_form(preview):
    p = preview
    request = Request(
        {"type": "http", "method": "GET", "path": "/fetch/fixture", "headers": [], "app": p.app}
    )
    response = report_entry_page(
        request,
        {"share_euid": p.share.euid, "report_bundle_root": "report/"},
        {"target_euid": "persisted-target-fixture", "relative_key": "report/multiqc.html"},
    )
    assert response.headers["referrer-policy"] == "strict-origin"
    assert b"form.method='POST'" in response.body
    assert b'referrerpolicy="no-referrer"' in response.body
    shell = ReportShell(response.body)
    assert len(shell.frames) == len(shell.scripts) == 1
    assert shell.frames[0]["name"] == "dewey-isolated-report"
    assert shell.scripts[0]["nonce"]
    policy = policy_directives(response)
    assert policy["script-src"] == {"'nonce-" + shell.scripts[0]["nonce"] + "'"}
    assert (
        policy["frame-src"]
        == policy["form-action"]
        == {"https://*." + p.settings.share_content_host_suffix}
    )
    assert policy["frame-ancestors"] == policy["base-uri"] == {"'none'"}
