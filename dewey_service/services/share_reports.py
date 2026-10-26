"""Authorized SQL sharing summaries; event totals never depend on GUI pagination."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from dewey_service.registry_access import owner_clause, principal
from dewey_service.services.share_policy import expiry


class ShareReportMixin:
    def _legacy_history_coverage(
        self,
        session,
        *,
        owner_subject=None,
        created_from=None,
        created_before=None,
        older_than_days=None,
        observed_at,
    ):
        """Preserved inactive records are counted without fabricating schema-3 fields."""
        from datetime import timedelta

        from daylily_tapdb import generic_instance
        from sqlalchemy import func, or_

        data, actor = generic_instance.json_addl, principal()
        query = self._share_query(session).filter(
            or_(data["schema_version"].astext.is_(None), data["schema_version"].astext != "3"),
            generic_instance.created_dt < observed_at,
        )
        if not actor.admin:
            query = query.filter(owner_clause(data, actor))
        if owner_subject:
            query = query.filter(data["owner_subject"].astext == owner_subject)
        if created_from is not None:
            query = query.filter(generic_instance.created_dt >= expiry(created_from))
        if created_before is not None:
            query = query.filter(generic_instance.created_dt < expiry(created_before))
        if older_than_days is not None:
            query = query.filter(
                generic_instance.created_dt < observed_at - timedelta(days=older_than_days)
            )
        groups = (
            query.with_entities(
                data["schema_version"].astext,
                data["status"].astext,
                generic_instance.bstatus,
                func.count(),
            )
            .group_by(
                data["schema_version"].astext, data["status"].astext, generic_instance.bstatus
            )
            .all()
        )
        return {
            "total": sum(row[3] for row in groups),
            "excluded_from_schema3_metrics": True,
            "groups": [
                {
                    "schema_version": schema,
                    "stored_status": status,
                    "native_status": native,
                    "count": count,
                }
                for schema, status, native, count in groups
            ],
            "filters_applied": [
                "owner_subject",
                "created_from",
                "created_before",
                "older_than_days",
            ],
            "access_coverage": "Historical identity/access schemas are not inferred",
        }

    def _report_population(
        self,
        session,
        *,
        owner_subject=None,
        status=None,
        audience=None,
        content_mode=None,
        created_from=None,
        created_before=None,
        older_than_days=None,
        never_accessed=False,
        observed_at=None,
    ):
        from datetime import timedelta

        from daylily_tapdb import generic_instance, generic_instance_lineage
        from sqlalchemy import DateTime, and_, case, cast, func, or_
        from sqlalchemy.orm import aliased

        actor, now = principal(), observed_at or datetime.now(timezone.utc)
        if owner_subject and owner_subject != actor.subject and not actor.admin:
            raise HTTPException(403, "Only administrators may select another sharing owner")
        if (
            status not in {None, "active", "revoked", "expired"}
            or audience not in {None, "recipients", "public_registered"}
            or content_mode not in {None, "download", "www"}
        ):
            raise ValueError("Invalid report filter")
        if older_than_days is not None and (
            type(older_than_days) is not int or older_than_days < 0
        ):
            raise ValueError("older_than_days must be a nonnegative integer")
        if type(never_accessed) is not bool:
            raise ValueError("never_accessed must be boolean")
        event, edge = aliased(generic_instance), aliased(generic_instance_lineage)
        detail = event.json_addl["details"]
        kind = event.json_addl["event_type"].astext
        successful_get = and_(
            or_(
                and_(
                    kind == "gateway_response_completed",
                    detail["status_code"].astext.in_(["200", "206"]),
                ),
                and_(kind == "gateway_condition_result", detail["status_code"].astext == "304"),
            ),
            func.coalesce(detail["method"].astext, detail["request_method"].astext) == "GET",
        )
        successful_access = or_(
            successful_get,
            and_(kind == "archive_completed", event.json_addl["decision"].astext == "completed"),
            and_(kind == "report_context_created", event.json_addl["decision"].astext == "allow"),
        )
        verified_actor = and_(
            event.json_addl["actor_email_verified"].astext == "true",
            event.json_addl["actor_service"].astext == "false",
        )
        activity = (
            session.query(
                edge.parent_instance_uid.label("share_uid"),
                func.max(event.created_dt).label("last_access"),
                func.count(
                    func.distinct(
                        case((verified_actor, event.json_addl["actor"].astext), else_=None)
                    )
                ).label("viewers"),
                func.count().filter(successful_get).label("successful_gets"),
                func.count().label("successful_accesses"),
            )
            .join(event, event.uid == edge.child_instance_uid)
            .filter(
                edge.relationship_type == "share_event",
                edge.is_deleted.is_(False),
                event.is_deleted.is_(False),
                event.type == "share_event",
                event.domain_code == self.backend.domain_code,
                event.created_dt < now,
                successful_access,
            )
            .group_by(edge.parent_instance_uid)
            .subquery()
        )
        data = generic_instance.json_addl
        shares = (
            self._share_query(session)
            .outerjoin(activity, activity.c.share_uid == generic_instance.uid)
            .filter(data["schema_version"].astext == "3", generic_instance.created_dt < now)
        )
        if not actor.admin:
            shares = shares.filter(owner_clause(data, actor))
        if owner_subject:
            shares = shares.filter(data["owner_subject"].astext == owner_subject)
        for name, value in (("audience", audience), ("content_mode", content_mode)):
            if value is not None:
                shares = shares.filter(data[name].astext == value)
        expired = cast(data["expires_at"].astext, DateTime(timezone=True)) <= now
        if status == "expired":
            shares = shares.filter(data["status"].astext == "active", expired)
        elif status == "active":
            shares = shares.filter(
                generic_instance.bstatus != "archived",
                data["status"].astext == "active",
                or_(data["expires_at"].astext.is_(None), ~expired),
            )
        elif status:
            shares = shares.filter(data["status"].astext == status)
        if created_from is not None:
            shares = shares.filter(generic_instance.created_dt >= expiry(created_from))
        if created_before is not None:
            shares = shares.filter(generic_instance.created_dt < expiry(created_before))
        if older_than_days is not None:
            shares = shares.filter(
                generic_instance.created_dt < now - timedelta(days=older_than_days)
            )
        if never_accessed:
            shares = shares.filter(activity.c.last_access.is_(None))
        return shares, activity

    @staticmethod
    def _inventory_digest(query, activity):
        from hashlib import sha256

        from daylily_tapdb import generic_instance
        from sqlalchemy import String, cast, func
        from sqlalchemy.dialects.postgresql import aggregate_order_by

        native = (
            query.with_entities(
                func.string_agg(
                    generic_instance.euid
                    + ":"
                    + cast(generic_instance.record_revision, String)
                    + ":"
                    + func.coalesce(cast(activity.c.last_access, String), "")
                    + ":"
                    + func.coalesce(cast(activity.c.viewers, String), "0")
                    + ":"
                    + func.coalesce(cast(activity.c.successful_gets, String), "0")
                    + ":"
                    + func.coalesce(cast(activity.c.successful_accesses, String), "0"),
                    aggregate_order_by("|", generic_instance.euid),
                )
            ).scalar()
            or ""
        )
        return sha256(native.encode()).hexdigest()

    def sharing_report(
        self,
        *,
        starts_at,
        ends_at=None,
        owner_subject=None,
        status=None,
        audience=None,
        content_mode=None,
        created_from=None,
        created_before=None,
        older_than_days=None,
        never_accessed=False,
    ):
        self._require_sharing()
        from daylily_tapdb import generic_instance, generic_instance_lineage
        from sqlalchemy import BigInteger, case, cast, func
        from sqlalchemy.orm import aliased

        start = expiry(starts_at)
        end = datetime.now(timezone.utc) if ends_at is None else expiry(ends_at)
        if starts_at is None or end <= start or end > datetime.now(timezone.utc):
            raise ValueError("Report requires a finite past start and an increasing finite end")
        if status is not None and status not in {"active", "revoked", "expired"}:
            raise ValueError("Invalid share status filter")
        if audience is not None and audience not in {"recipients", "public_registered"}:
            raise ValueError("Invalid audience filter")
        if content_mode is not None and content_mode not in {"download", "www"}:
            raise ValueError("Invalid content mode filter")
        actor = principal()
        if owner_subject is not None and owner_subject != actor.subject and not actor.admin:
            raise HTTPException(403, "Only administrators may select another sharing owner")
        with self.backend.session_scope(commit=False) as session:
            observed = datetime.now(timezone.utc)
            share = generic_instance
            data = share.json_addl
            shares, activity = self._report_population(
                session,
                owner_subject=owner_subject,
                status=status,
                audience=audience,
                content_mode=content_mode,
                created_from=created_from,
                created_before=created_before,
                older_than_days=older_than_days,
                never_accessed=never_accessed,
                observed_at=observed,
            )
            population_digest = self._inventory_digest(shares, activity)
            from sqlalchemy import DateTime

            expired = cast(data["expires_at"].astext, DateTime(timezone=True)) <= observed
            share_ids = shares.with_entities(share.uid).subquery()
            count = shares.count()
            durations = shares.with_entities(
                func.count().filter(data["expires_at"].astext.is_(None)),
                func.avg(
                    func.extract(
                        "epoch",
                        cast(data["expires_at"].astext, DateTime(timezone=True)) - share.created_dt,
                    )
                ),
            ).one()
            kinds = (
                shares.with_entities(
                    data["audience"].astext,
                    data["content_mode"].astext,
                    data["status"].astext,
                    func.count(),
                )
                .group_by(
                    data["audience"].astext, data["content_mode"].astext, data["status"].astext
                )
                .all()
            )
            duration_days = (
                func.extract(
                    "epoch",
                    cast(data["expires_at"].astext, DateTime(timezone=True)) - share.created_dt,
                )
                / 86400
            )
            duration_band = case(
                (data["expires_at"].astext.is_(None), "indefinite"),
                (duration_days <= 7, "up_to_7_days"),
                (duration_days <= 30, "over_7_up_to_30_days"),
                (duration_days <= 90, "over_30_up_to_90_days"),
                (duration_days <= 365, "over_90_up_to_365_days"),
                else_="over_365_days",
            )
            duration_buckets = {
                band: number
                for band, number in shares.with_entities(duration_band, func.count())
                .group_by(duration_band)
                .all()
            }
            current_status = case(
                (share.bstatus == "archived", "archived"),
                (data["status"].astext == "revoked", "revoked"),
                (expired, "expired"),
                else_=data["status"].astext,
            )
            lifecycle = {
                state: number
                for state, number in shares.with_entities(current_status, func.count())
                .group_by(current_status)
                .all()
            }
            created_in_window = shares.filter(
                share.created_dt >= start, share.created_dt < end
            ).count()
            never_count = shares.filter(activity.c.last_access.is_(None)).count()
            last_access = shares.with_entities(func.max(activity.c.last_access)).scalar()
            event, edge = aliased(generic_instance), aliased(generic_instance_lineage)
            events = (
                session.query(event)
                .join(edge, edge.child_instance_uid == event.uid)
                .filter(
                    edge.parent_instance_uid.in_(share_ids.select()),
                    edge.relationship_type == "share_event",
                    edge.is_deleted.is_(False),
                    event.is_deleted.is_(False),
                    event.type == "share_event",
                    event.domain_code == self.backend.domain_code,
                    event.created_dt >= start,
                    event.created_dt < end,
                )
            )
            payload = event.json_addl
            detail = payload["details"]
            grouping = [
                payload["event_type"].astext,
                payload["decision"].astext,
                func.coalesce(detail["request_method"].astext, detail["method"].astext, "unknown"),
                func.coalesce(detail["status_code"].astext, "unknown"),
                func.coalesce(detail["inline_report"].astext, "false"),
            ]
            event_groups = (
                events.with_entities(
                    *grouping,
                    func.count(),
                    func.coalesce(
                        func.sum(
                            cast(
                                func.coalesce(
                                    detail["server_bytes_sent"].astext,
                                    detail["bytes_sent"].astext,
                                    "0",
                                ),
                                BigInteger,
                            )
                        ),
                        0,
                    ),
                )
                .group_by(*grouping)
                .all()
            )
            watermark = events.with_entities(func.max(event.created_dt)).scalar()
            metrics = {
                "events": 0,
                "authorization_evaluations": 0,
                "denials": 0,
                "file_responses_completed": 0,
                "report_entries": 0,
                "report_sidecars": 0,
                "head_responses": 0,
                "not_modified_responses": 0,
                "range_responses": 0,
                "archive_attempts": 0,
                "archive_completions": 0,
                "server_bytes_sent": 0,
                "client_downloads_completed": None,
            }
            groups = []
            for kind, decision, method, code, inline_report, number, sent in event_groups:
                metrics["events"] += number
                metrics["denials"] += number if decision == "deny" else 0
                metrics["authorization_evaluations"] += number if kind == "authorization" else 0
                metrics["report_entries"] += number if kind == "report_context_created" else 0
                metrics["report_sidecars"] += (
                    number
                    if kind == "gateway_response_completed" and inline_report == "true"
                    else 0
                )
                metrics["archive_attempts"] += number if kind == "archive_started" else 0
                metrics["archive_completions"] += number if kind == "archive_completed" else 0
                if kind in {
                    "gateway_response_completed",
                    "gateway_disconnect_or_failure",
                    "gateway_condition_result",
                    "archive_completed",
                    "archive_interrupted",
                }:
                    metrics["server_bytes_sent"] += int(sent)
                    metrics["head_responses"] += number if method == "HEAD" else 0
                    metrics["not_modified_responses"] += number if code == "304" else 0
                    metrics["range_responses"] += number if code == "206" else 0
                    metrics["file_responses_completed"] += (
                        number
                        if kind == "gateway_response_completed"
                        and method == "GET"
                        and code in {"200", "206"}
                        and inline_report != "true"
                        else 0
                    )
                groups.append(
                    {
                        "event_type": kind,
                        "decision": decision,
                        "method": method,
                        "status_code": code,
                        "inline_report": inline_report == "true",
                        "count": number,
                        "server_bytes_sent": int(sent),
                    }
                )
            legacy = self._legacy_history_coverage(
                session,
                owner_subject=owner_subject,
                created_from=created_from,
                created_before=created_before,
                older_than_days=older_than_days,
                observed_at=observed,
            )
            if self._inventory_digest(shares, activity) != population_digest:
                raise HTTPException(
                    409, "Report population changed during read; request a fresh report"
                )
            return {
                "window": {
                    "starts_at": start.isoformat(),
                    "ends_at": end.isoformat(),
                    "end_exclusive": True,
                },
                "coverage": {
                    "schema_version": 3,
                    "complete": True,
                    "event_watermark": watermark.isoformat() if watermark else None,
                    "observed_at": observed.isoformat(),
                    "inventory_sha256": population_digest,
                    "share_counts": "current authorized schema3 state at observed_at",
                    "event_counts": "native events in the requested window",
                    "verified_viewers": "Only events with explicit verified non-service actor evidence",
                    "historical_legacy": legacy,
                    "client_persistence_observed": False,
                    "raw_presign_consumption_observed": False,
                },
                "shares": {
                    "total": count,
                    "indefinite": durations[0],
                    "created_in_window": created_in_window,
                    "current_lifecycle_counts": lifecycle,
                    "duration_buckets": duration_buckets,
                    "never_accessed": never_count,
                    "last_successful_access": last_access.isoformat() if last_access else None,
                    "mean_finite_duration_seconds": float(durations[1])
                    if durations[1] is not None
                    else None,
                    "groups": [
                        {"audience": a, "content_mode": c, "status": s, "count": n}
                        for a, c, s, n in kinds
                    ],
                },
                "metrics": metrics,
                "event_groups": groups,
            }

    def sharing_inventory(
        self,
        *,
        owner_subject=None,
        status=None,
        audience=None,
        content_mode=None,
        created_from=None,
        created_before=None,
        older_than_days=None,
        never_accessed=False,
        page=1,
        page_size=100,
        observed_at=None,
        expected_inventory_sha256=None,
    ):
        """Bounded owner-authorized lifecycle drilldown; pages expose their coverage."""
        self._require_sharing()
        if (
            type(page) is not int
            or page < 1
            or type(page_size) is not int
            or not 1 <= page_size <= 200
        ):
            raise ValueError("page must be positive and page_size must be 1..200")
        from daylily_tapdb import generic_instance

        from dewey_service.tapdb_backend import normalize_instance_payload

        now = datetime.now(timezone.utc) if observed_at is None else expiry(observed_at)
        if now > datetime.now(timezone.utc):
            raise ValueError("observed_at must not be in the future")
        with self.backend.session_scope(commit=False) as session:
            shares, activity = self._report_population(
                session,
                owner_subject=owner_subject,
                status=status,
                audience=audience,
                content_mode=content_mode,
                created_from=created_from,
                created_before=created_before,
                older_than_days=older_than_days,
                never_accessed=never_accessed,
                observed_at=now,
            )
            inventory_sha256 = self._inventory_digest(shares, activity)
            if (
                expected_inventory_sha256 is not None
                and expected_inventory_sha256 != inventory_sha256
            ):
                raise HTTPException(409, "Report inventory changed; restart the export")
            total = shares.count()
            rows = (
                shares.with_entities(
                    generic_instance,
                    activity.c.last_access,
                    activity.c.viewers,
                    activity.c.successful_gets,
                    activity.c.successful_accesses,
                )
                .order_by(generic_instance.created_dt, generic_instance.euid)
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            items = []
            for share, last, viewers, gets, accesses in rows:
                data = normalize_instance_payload(share)
                counts = {"email": 0, "domain": 0, "registered": 0}
                for grant in self._share_grants(session, share):
                    rule = normalize_instance_payload(grant)
                    if (
                        rule.get("status") == "active"
                        and rule.get("policy_revision") == data["policy_revision"]
                        and expiry(rule["expires_at"]) > now
                    ):
                        counts[rule["recipient_type"]] += 1
                state = "archived" if share.bstatus == "archived" else data["status"]
                if state == "active" and expiry(data["expires_at"]) <= now:
                    state = "expired"
                items.append(
                    {
                        "share_euid": share.euid,
                        "name": share.name,
                        "owner_subject": data["owner_subject"],
                        "audience": data["audience"],
                        "content_mode": data["content_mode"],
                        "status": state,
                        "created_at": share.created_dt.isoformat(),
                        "age_days": (now - share.created_dt).total_seconds() / 86400,
                        "expires_at": data["expires_at"],
                        "duration_days": None
                        if data["expires_at"] is None
                        else (expiry(data["expires_at"]) - share.created_dt).total_seconds()
                        / 86400,
                        "last_successful_access": last.isoformat() if last else None,
                        "never_accessed": last is None,
                        "unique_verified_viewers": int(viewers or 0),
                        "successful_get_responses": int(gets or 0),
                        "successful_access_events": int(accesses or 0),
                        "recipient_grant_counts": counts,
                        "public_registered_population_unbounded": data["audience"]
                        == "public_registered",
                        "fetch_path": "/fetch/" + share.euid,
                        "management_path": "/shares/" + share.euid,
                    }
                )
            if self._inventory_digest(shares, activity) != inventory_sha256:
                raise HTTPException(409, "Report inventory changed during read; restart the export")
            return {
                "items": items,
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": page * page_size < total,
                "inventory_sha256": inventory_sha256,
                "observed_at": now.isoformat(),
                "complete": page == 1 and total <= page_size,
                "coverage": "current authorized schema3 share state; successful GET/archive/report-entry events strictly before observed_at; verified viewers require explicit actor evidence",
                "historical_legacy": self._legacy_history_coverage(
                    session,
                    owner_subject=owner_subject,
                    created_from=created_from,
                    created_before=created_before,
                    older_than_days=older_than_days,
                    observed_at=now,
                ),
            }
