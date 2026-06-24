"""
Rule-based Cisco IOS command generation.

This module intentionally uses only pure Python. The CommandEngine class exposes
a small stable interface that can later be backed by an AI model without
changing callers such as voice recognition, FastAPI, or a web frontend.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable


CommandResult = dict[str, str]
Matcher = Callable[[list[str], str], CommandResult | None]


@dataclass(frozen=True)
class CommandRule:
    """A named command rule and the function that attempts to match it."""

    name: str
    matcher: Matcher


class CommandEngine:
    """Convert natural language networking instructions into Cisco IOS commands."""

    UNKNOWN_RESULT: CommandResult = {
        "intent": "unknown",
        "command": "Unknown command",
    }

    def __init__(self) -> None:
        self._rules: tuple[CommandRule, ...] = (
            CommandRule("show_interfaces", self._match_show_interfaces),
            CommandRule("show_ip_interfaces", self._match_show_ip_interfaces),
            CommandRule("show_version", self._match_show_version),
            CommandRule("show_running_config", self._match_show_running_config),
            CommandRule("shutdown_interface", self._match_shutdown_interface),
            CommandRule("enable_interface", self._match_enable_interface),
        )

    def generate(self, user_input: str) -> CommandResult:
        """Return the detected intent and Cisco IOS command for user_input."""

        normalized_text = self._normalize_text(user_input)
        tokens = normalized_text.split()

        for rule in self._rules:
            result = rule.matcher(tokens, normalized_text)
            if result is not None:
                return result

        return dict(self.UNKNOWN_RESULT)

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize case, spacing, and common punctuation noise."""

        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9/\s-]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _result(intent: str, command: str) -> CommandResult:
        return {
            "intent": intent,
            "command": command,
        }

    @staticmethod
    def _contains_any(tokens: Iterable[str], words: set[str]) -> bool:
        return any(token in words for token in tokens)

    @staticmethod
    def _has_interface_word(tokens: Iterable[str]) -> bool:
        return any(token in {"interface", "interfaces"} for token in tokens)

    @staticmethod
    def _format_interface_name(raw_interface: str) -> str:
        """Convert common spoken or typed interface names to Cisco casing."""

        compact = raw_interface.replace(" ", "").replace("-", "")
        compact_lower = compact.lower()

        interface_prefixes = {
            "gigabitethernet": "GigabitEthernet",
            "fastethernet": "FastEthernet",
            "ethernet": "Ethernet",
            "serial": "Serial",
            "loopback": "Loopback",
            "vlan": "Vlan",
        }

        for raw_prefix, cisco_prefix in interface_prefixes.items():
            if compact_lower.startswith(raw_prefix):
                return cisco_prefix + compact[len(raw_prefix) :]

        return compact

    def _match_show_interfaces(
        self,
        tokens: list[str],
        normalized_text: str,
    ) -> CommandResult | None:
        action_words = {"show", "display", "list", "view"}
        scope_words = {"all", "every"}

        if not self._contains_any(tokens, action_words):
            return None

        if self._has_interface_word(tokens) and (
            self._contains_any(tokens, scope_words)
            or "ip" not in tokens
            or normalized_text in {"show interfaces", "display interfaces"}
        ):
            return self._result("show_interfaces", "show interfaces")

        return None

    def _match_show_ip_interfaces(
        self,
        tokens: list[str],
        normalized_text: str,
    ) -> CommandResult | None:
        action_words = {"show", "display", "list", "view"}

        if not self._contains_any(tokens, action_words):
            return None

        ip_interface_phrases = {
            "show ip",
            "display ip",
            "show ip interface",
            "show ip interfaces",
            "show ip interface brief",
            "display ip interface brief",
        }

        if normalized_text in ip_interface_phrases:
            return self._result("show_ip_interfaces", "show ip interface brief")

        if "ip" in tokens and self._has_interface_word(tokens):
            return self._result("show_ip_interfaces", "show ip interface brief")

        return None

    def _match_show_version(
        self,
        tokens: list[str],
        normalized_text: str,
    ) -> CommandResult | None:
        del normalized_text

        action_words = {"show", "display", "view"}
        if self._contains_any(tokens, action_words) and "version" in tokens:
            return self._result("show_version", "show version")

        return None

    def _match_show_running_config(
        self,
        tokens: list[str],
        normalized_text: str,
    ) -> CommandResult | None:
        del normalized_text

        action_words = {"show", "display", "view"}
        config_words = {"config", "configuration", "running-config"}

        if (
            self._contains_any(tokens, action_words)
            and "running" in tokens
            and self._contains_any(tokens, config_words)
        ):
            return self._result("show_running_config", "show running-config")

        return None

    def _match_shutdown_interface(
        self,
        tokens: list[str],
        normalized_text: str,
    ) -> CommandResult | None:
        del tokens
        return self._match_interface_state_change(
            normalized_text=normalized_text,
            intent="shutdown_interface",
            ios_action="shutdown",
            action_words=("shutdown", "shut down", "disable"),
        )

    def _match_enable_interface(
        self,
        tokens: list[str],
        normalized_text: str,
    ) -> CommandResult | None:
        del tokens
        return self._match_interface_state_change(
            normalized_text=normalized_text,
            intent="enable_interface",
            ios_action="no shutdown",
            action_words=("enable", "turn on", "activate", "no shutdown"),
        )

    def _match_interface_state_change(
        self,
        normalized_text: str,
        intent: str,
        ios_action: str,
        action_words: tuple[str, ...],
    ) -> CommandResult | None:
        if not any(action_word in normalized_text for action_word in action_words):
            return None

        interface_name = self._extract_interface_name(normalized_text)
        if interface_name is None:
            return None

        command = (
            "configure terminal\n"
            f"interface {interface_name}\n"
            f"{ios_action}"
        )
        return self._result(intent, command)

    def _extract_interface_name(self, normalized_text: str) -> str | None:
        interface_pattern = re.compile(
            r"\b(?:interface|interfaces)\s+"
            r"(?P<interface>"
            r"(?:gigabitethernet|fastethernet|ethernet|serial|loopback|vlan)"
            r"\s*[0-9][0-9/\s.-]*"
            r")\b"
        )
        match = interface_pattern.search(normalized_text)

        if match is None:
            return None

        return self._format_interface_name(match.group("interface"))

