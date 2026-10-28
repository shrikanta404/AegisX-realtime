from typing import Any


class ChangeDetector:
    def compare_services(self, previous_services: list[dict[str, Any]], current_services: list[dict[str, Any]]) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        previous_map = {(item.get("port"), item.get("protocol")): item for item in previous_services}
        current_map = {(item.get("port"), item.get("protocol")): item for item in current_services}

        for key, current in current_map.items():
            if key not in previous_map:
                changes.append({
                    "asset_type": "service",
                    "asset_identifier": f"{current.get('host', 'unknown')}:{current.get('port')}",
                    "change_type": "new_service",
                    "previous_state": None,
                    "current_state": current,
                })

        for key, previous in previous_map.items():
            if key not in current_map:
                changes.append({
                    "asset_type": "service",
                    "asset_identifier": f"{previous.get('host', 'unknown')}:{previous.get('port')}",
                    "change_type": "service_removed",
                    "previous_state": previous,
                    "current_state": None,
                })

        for key in previous_map.keys() & current_map.keys():
            previous = previous_map[key]
            current = current_map[key]
            if previous.get("state") != current.get("state"):
                changes.append({
                    "asset_type": "service",
                    "asset_identifier": f"{current.get('host', 'unknown')}:{current.get('port')}",
                    "change_type": "service_state_changed",
                    "previous_state": previous,
                    "current_state": current,
                })
            elif (
                previous.get("service_name") != current.get("service_name")
                or previous.get("version") != current.get("version")
            ):
                changes.append({
                    "asset_type": "service",
                    "asset_identifier": f"{current.get('host', 'unknown')}:{current.get('port')}",
                    "change_type": "service_changed",
                    "previous_state": previous,
                    "current_state": current,
                })
        return changes

    def compare_dns(self, previous_records: list[dict[str, Any]], current_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        previous_map = {(r.get("record_type"), r.get("name"), r.get("value")): r for r in previous_records}
        current_map = {(r.get("record_type"), r.get("name"), r.get("value")): r for r in current_records}

        for key, current in current_map.items():
            if key not in previous_map:
                changes.append({
                    "asset_type": "dns",
                    "asset_identifier": f"{current.get('name')} {current.get('record_type')} {current.get('value')}",
                    "change_type": "dns_record_added",
                    "previous_state": None,
                    "current_state": current,
                })

        for key, previous in previous_map.items():
            if key not in current_map:
                changes.append({
                    "asset_type": "dns",
                    "asset_identifier": f"{previous.get('name')} {previous.get('record_type')} {previous.get('value')}",
                    "change_type": "dns_record_removed",
                    "previous_state": previous,
                    "current_state": None,
                })
        return changes

    def compare_tls(self, previous_tls: dict[str, Any] | None, current_tls: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not previous_tls or not current_tls:
            return []
        if "error" in previous_tls or "error" in current_tls:
            return []

        fields = ["subject", "issuer", "serial_number", "valid_from", "valid_until", "fingerprint", "is_expired"]
        changed_fields: list[dict[str, Any]] = []
        for field in fields:
            previous_value = previous_tls.get(field)
            current_value = current_tls.get(field)
            if previous_value != current_value:
                changed_fields.append({
                    "field": field,
                    "previous": previous_value,
                    "current": current_value,
                })

        if not changed_fields:
            return []

        return [{
            "asset_type": "tls",
            "asset_identifier": current_tls.get("domain") or previous_tls.get("domain") or previous_tls.get("subject") or "unknown",
            "change_type": "tls_certificate_changed",
            "previous_state": previous_tls,
            "current_state": current_tls,
            "changed_fields": changed_fields,
        }]
