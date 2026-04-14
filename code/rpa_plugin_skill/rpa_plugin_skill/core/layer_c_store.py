from __future__ import annotations

from dataclasses import dataclass

from typedb.driver import TransactionType

from .config import AppConfig
from .layer_c_migrations import apply_layer_c_migrations
from .typedb_bootstrap import connect_with_retry


class SecretReferenceError(ValueError):
    """Raised when a credential secret reference looks like plaintext."""


ALLOWED_SECRET_PREFIXES: dict[str, tuple[str, ...]] = {
    "env": ("env://",),
    "vault": ("vault://",),
    "openclaw_secret": ("openclaw://", "openclaw-secret://"),
    "other": ("ref://",),
}


@dataclass(frozen=True)
class RegisteredSourceInput:
    registration_id: str
    source_name: str
    source_kind: str
    source_url: str
    source_description: str
    source_is_active: bool
    credential_ref_id: str
    secret_provider: str
    secret_ref: str


class LayerCStore:
    """Typed data-access layer for Layer C entities only."""

    def __init__(self, config: AppConfig, ensure_schema: bool = True):
        self.config = config
        if ensure_schema:
            apply_layer_c_migrations(config)

    def _validate_secret_ref(self, provider: str, secret_ref: str) -> None:
        prefixes = ALLOWED_SECRET_PREFIXES.get(provider)
        if not prefixes:
            raise SecretReferenceError(f"Unsupported secret provider: {provider}")
        if not any(secret_ref.startswith(prefix) for prefix in prefixes):
            raise SecretReferenceError(
                "Secret references must be provider refs (env://, vault://, openclaw://, ref://), "
                "not plaintext values"
            )

    def upsert_registered_source(self, data: RegisteredSourceInput) -> None:
        self._validate_secret_ref(data.secret_provider, data.secret_ref)
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''put
  $source isa gr_registered_source,
    has gr_registration_id "{data.registration_id}",
    has gr_source_name "{data.source_name}",
    has gr_source_kind "{data.source_kind}",
    has gr_source_url "{data.source_url}",
    has gr_source_description "{data.source_description}",
    has gr_source_is_active {str(data.source_is_active).lower()};

  $cred isa gr_credential_ref,
    has gr_credential_ref_id "{data.credential_ref_id}",
    has gr_secret_provider "{data.secret_provider}",
    has gr_secret_ref "{data.secret_ref}";'''
                ).resolve()

                tx.query(
                    f'''match
  $source isa gr_registered_source, has gr_registration_id "{data.registration_id}";
  $cred isa gr_credential_ref, has gr_credential_ref_id "{data.credential_ref_id}";
put
  (source: $source, credential: $cred) isa gr_source_credential_binding;'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def upsert_rule(
        self,
        registration_id: str,
        rule_id: str,
        rule_name: str,
        nl_text: str,
        horn_text: str,
        typeql_fun: str,
        ast_ref: str,
        status: str,
    ) -> None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''put
  $rule isa gr_rule_definition,
    has gr_rule_id "{rule_id}",
    has gr_rule_name "{rule_name}",
    has gr_rule_nl_text "{nl_text}",
    has gr_rule_horn_text "{horn_text}",
    has gr_rule_typeql_fun "{typeql_fun}",
    has gr_rule_ast_ref "{ast_ref}",
    has gr_rule_status "{status}";'''
                ).resolve()
                tx.query(
                    f'''match
  $source isa gr_registered_source, has gr_registration_id "{registration_id}";
  $rule isa gr_rule_definition, has gr_rule_id "{rule_id}";
put
  (source: $source, rule: $rule) isa gr_source_rule_binding;'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def set_rule_status(self, rule_id: str, status: str) -> None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''match
  $rule isa gr_rule_definition,
    has gr_rule_id "{rule_id}",
    has gr_rule_status $old;
delete
  $rule has $old;
insert
  $rule has gr_rule_status "{status}";'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def delete_rule(self, registration_id: str, rule_id: str) -> None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''match
  $source isa gr_registered_source, has gr_registration_id "{registration_id}";
  $rule isa gr_rule_definition, has gr_rule_id "{rule_id}";
  $binding (source: $source, rule: $rule) isa gr_source_rule_binding;
delete
  $binding;'''
                ).resolve()
                tx.query(
                    f'''match
  $rule isa gr_rule_definition, has gr_rule_id "{rule_id}";
delete
  $rule;'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def upsert_task(
        self,
        registration_id: str,
        task_id: str,
        task_name: str,
        task_description: str,
        extract_plan_ref: str,
        status: str,
    ) -> None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''match
  $task isa gr_task_definition, has gr_task_id "{task_id}";
delete
  $task;'''
                ).resolve()
                tx.query(
                    f'''put
  $task isa gr_task_definition,
    has gr_task_id "{task_id}",
    has gr_task_name "{task_name}",
    has gr_task_description "{task_description}",
    has gr_extract_plan_ref "{extract_plan_ref}",
    has gr_task_status "{status}";'''
                ).resolve()
                tx.query(
                    f'''match
  $source isa gr_registered_source, has gr_registration_id "{registration_id}";
  $task isa gr_task_definition, has gr_task_id "{task_id}";
put
  (source: $source, task: $task) isa gr_source_task_binding;'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def set_task_status(self, task_id: str, status: str) -> None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''match
  $task isa gr_task_definition,
    has gr_task_id "{task_id}",
    has gr_task_status $old;
delete
  $task has $old;
insert
  $task has gr_task_status "{status}";'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def delete_task(self, registration_id: str, task_id: str) -> None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''match
  $source isa gr_registered_source, has gr_registration_id "{registration_id}";
  $task isa gr_task_definition, has gr_task_id "{task_id}";
  $binding (source: $source, task: $task) isa gr_source_task_binding;
delete
  $binding;'''
                ).resolve()
                tx.query(
                    f'''match
  $task isa gr_task_definition, has gr_task_id "{task_id}";
delete
  $task;'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def upsert_setting(self, key: str, value: str) -> None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''match
  $existing isa gr_setting, has gr_setting_key "{key}";
delete
  $existing;'''
                ).resolve()
                tx.query(
                    f'''insert
  $setting isa gr_setting,
    has gr_setting_key "{key}",
    has gr_setting_value "{value}";'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def upsert_agent_profile(self, profile_id: str, name: str, email: str) -> None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.WRITE) as tx:
                tx.query(
                    f'''put
  $profile isa gr_agent_profile,
    has gr_agent_profile_id "{profile_id}",
    has gr_agent_name "{name}",
    has gr_agent_email "{email}";'''
                ).resolve()
                tx.commit()
        finally:
            driver.close()

    def fetch_setting(self, key: str) -> str | None:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.READ) as tx:
                answer = tx.query(
                    f'''match
  $setting isa gr_setting,
    has gr_setting_key "{key}",
    has gr_setting_value $value;
fetch {{
  "value": $value
}};'''
                ).resolve()
                if not answer.is_concept_documents():
                    return None
                docs = list(answer.as_concept_documents())
                if not docs:
                    return None
                raw = docs[0].get("value")
                return str(raw) if raw is not None else None
        finally:
            driver.close()

    def fetch_registered_sources(self) -> list[dict]:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.READ) as tx:
                answer = tx.query(
                    '''match
  $s isa gr_registered_source,
    has gr_registration_id $id,
    has gr_source_name $name,
    has gr_source_kind $kind,
    has gr_source_url $url,
    has gr_source_is_active $active;
fetch {
  "registration_id": $id,
  "source_name": $name,
  "source_kind": $kind,
  "source_url": $url,
  "source_is_active": $active
};'''
                ).resolve()
                if not answer.is_concept_documents():
                    return []
                return list(answer.as_concept_documents())
        finally:
            driver.close()

    def fetch_rules_for_source(self, registration_id: str) -> list[dict]:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.READ) as tx:
                answer = tx.query(
                    f'''match
  $source isa gr_registered_source, has gr_registration_id "{registration_id}";
  $binding (source: $source, rule: $rule) isa gr_source_rule_binding;
  $rule has gr_rule_id $id,
    has gr_rule_name $name,
    has gr_rule_nl_text $nl,
    has gr_rule_horn_text $horn,
    has gr_rule_typeql_fun $typeql,
    has gr_rule_ast_ref $ast,
    has gr_rule_status $status;
fetch {{
  "rule_id": $id,
  "rule_name": $name,
  "rule_nl_text": $nl,
  "rule_horn_text": $horn,
  "rule_typeql_fun": $typeql,
  "rule_ast_ref": $ast,
  "rule_status": $status
}};'''
                ).resolve()
                if not answer.is_concept_documents():
                    return []
                return list(answer.as_concept_documents())
        finally:
            driver.close()

    def fetch_tasks_for_source(self, registration_id: str) -> list[dict]:
        driver = connect_with_retry(self.config)
        try:
            with driver.transaction(self.config.layer_c_db, TransactionType.READ) as tx:
                answer = tx.query(
                    f'''match
  $source isa gr_registered_source, has gr_registration_id "{registration_id}";
  $binding (source: $source, task: $task) isa gr_source_task_binding;
  $task has gr_task_id $id,
    has gr_task_name $name,
    has gr_task_description $description,
    has gr_extract_plan_ref $extract_plan_ref,
    has gr_task_status $status;
fetch {{
  "task_id": $id,
  "task_name": $name,
  "task_description": $description,
  "extract_plan_ref": $extract_plan_ref,
  "task_status": $status
}};'''
                ).resolve()
                if not answer.is_concept_documents():
                    return []
                return list(answer.as_concept_documents())
        finally:
            driver.close()
