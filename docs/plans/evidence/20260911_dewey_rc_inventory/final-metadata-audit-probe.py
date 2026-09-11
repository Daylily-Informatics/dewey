"""One actual native update in a transaction that must roll back; emit no row values."""
import datetime as dt
import hashlib
import json
from pathlib import Path

from dewey_rehearsal_copy import ROOT, cfg_at, new_json
from dewey_xrf_template_setup_port_fix import frozen_source
from dewey_metadata_conversion import convert_payload
from daylily_tapdb.identity_inventory import content_hash
from daylily_tapdb.models.audit import audit_log
from daylily_tapdb.models.instance import generic_instance
from daylily_tapdb.runtime_principal import operator_connection
from daylily_tapdb.security_context import TapdbTransactionContext, apply_transaction_context, assert_operator_role
from daylily_tapdb.services.object_operations import ObjectSelector, update_object
from sqlalchemy import Text, cast, func, select, text
from sqlalchemy.orm import Session


class ProbeRollback(Exception):
    pass


cfg = cfg_at('replacement-operator.yaml', 'dewey_prod_tapdb10')
frozen_source(cfg_at('control-operator.yaml', 'postgres'))
plan_path = ROOT / 'receipts/final-metadata-conversion/metadata-plan.json'
plan = json.loads(plan_path.read_text())
item = plan['changes'][0]
assert item['table'] == 'generic_instance'
result = {'plan_file_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(), 'uid': item['uid']}
try:
    with operator_connection(cfg, isolation_level='REPEATABLE READ') as connection:
        assert connection.execute(text('SELECT oid FROM pg_database WHERE datname=current_database()')).scalar_one() == 646741
        assert connection.execute(text('SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()')).scalar_one() == 0
        with Session(bind=connection, expire_on_commit=False) as session:
            apply_transaction_context(session, TapdbTransactionContext(config_identity=str(ROOT / 'replacement-operator.yaml'), schema_name=cfg['schema_name'], domain_code='M', owner_repo_name='dewey', tenant_id=None, actor='dewey-tapdb10-migration', allow_global_rows=False), assert_runtime_role=False)
            assert_operator_role(session, schema_name=cfg['schema_name'], operator_user='dayhoff')
            obj = session.execute(select(generic_instance).where(generic_instance.uid == item['uid']).with_for_update()).scalar_one()
            raw = session.execute(select(cast(func.to_jsonb(generic_instance.json_addl), Text)).where(generic_instance.uid == item['uid'])).scalar_one()
            assert content_hash(json.loads(raw, parse_float=str)) == item['json_before']
            audit_before = session.execute(select(func.max(audit_log.uid))).scalar_one()
            timestamp = session.execute(select(cast(func.to_jsonb(func.current_timestamp()), Text))).scalar_one()
            proposed, _ = convert_payload(obj.json_addl)
            update_object(session, ObjectSelector(uid=item['uid'], record_type='instance'), {'json_addl': proposed}, actor='dewey-tapdb10-migration', dry_run=False)
            raw_json, raw_modified = session.execute(select(cast(func.to_jsonb(generic_instance.json_addl), Text), cast(func.to_jsonb(generic_instance.modified_dt), Text)).where(generic_instance.uid == item['uid'])).one()
            result['planned_json_matches'] = content_hash(json.loads(raw_json, parse_float=str)) == item['json_after']
            result['transaction_timestamp_matches'] = json.loads(raw_modified) == json.loads(timestamp)
            rows = [json.loads(v) for v in session.execute(select(cast(func.to_jsonb(audit_log.__table__.table_valued()), Text)).where(audit_log.uid > audit_before)).scalars()]
            result['audit_count'] = len(rows)
            result['audit_columns'] = sorted(v['column_name'] for v in rows)
            result['audit_actor_matches'] = all(v['changed_by'] == 'dewey-tapdb10-migration' for v in rows)
            creation = [v for v in rows if v['column_name'] == 'created_dt']
            result['creation_audit_same_instant'] = len(creation) == 1 and dt.datetime.fromisoformat(creation[0]['old_value']) == dt.datetime.fromisoformat(creation[0]['new_value']) == obj.created_dt
            result['audit_before_uid'] = audit_before
            raise ProbeRollback()
except ProbeRollback:
    result['rollback_acknowledged'] = True
new_json(ROOT / 'receipts/final-metadata-conversion/audit-probe.json', result)
print(json.dumps(result))
