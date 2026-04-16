from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

import httpx

from ..core.settings import Settings
from ..domain.models import ProjectSeed


@dataclass(slots=True)
class EvidenceGroundedChatService:
    settings: Settings

    def build_reply(self, project: ProjectSeed, prompt: str) -> str:
        evidence_context = self._assemble_context(project, prompt)
        if not self.settings.openai_api_key:
            return (
                "Chat is configured for evidence-grounded OpenAI responses, but `OPENAI_API_KEY` is missing. "
                "Add it in the environment to enable stakeholder chat for this workspace."
            )
        if not evidence_context:
            return (
                "This project does not have enough evidence yet to answer safely. "
                "Connect a source, run ingestion, and retry the question."
            )

        system_prompt = dedent(
            """
            You are the Cloud Migration Cockpit stakeholder assistant.
            Answer only from the supplied evidence and report excerpts.
            If the evidence is insufficient, say so directly instead of guessing.
            Keep answers concise, executive-friendly, and evidence-backed.
            End with a `Sources:` line that lists the most relevant source URIs.
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Project: {project.overview.name}
            Client: {project.overview.client_name}
            Question: {prompt}

            Evidence:
            {evidence_context}
            """
        ).strip()

        try:
            payload = {
                "model": self.settings.openai_model,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    f"{self.settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            return (
                "The stakeholder assistant is configured, but the OpenAI request failed. "
                f"No answer was generated. Error: {exc.__class__.__name__}."
            )

        choices = body.get("choices", [])
        if not choices:
            return (
                "The stakeholder assistant did not receive a usable response from OpenAI. "
                "No answer was generated."
            )

        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(str(item.get("text", "")))
            content = "\n".join(part for part in text_parts if part).strip()

        if isinstance(content, str) and content.strip():
            return content.strip()

        return (
            "The stakeholder assistant returned an empty response. "
            "No answer was generated."
        )

    def _assemble_context(self, project: ProjectSeed, prompt: str) -> str:
        normalized_prompt = prompt.lower()
        tokens = {token for token in normalized_prompt.replace("/", " ").replace("-", " ").split() if len(token) > 2}

        scored_findings: list[tuple[int, str]] = []
        for finding in project.findings:
            haystack = " ".join(
                [
                    finding.title.lower(),
                    finding.summary.lower(),
                    finding.recommendation.lower(),
                    " ".join(reference.source_uri.lower() for reference in finding.evidence),
                    " ".join(reference.excerpt.lower() for reference in finding.evidence),
                ]
            )
            score = sum(1 for token in tokens if token in haystack)
            if score == 0 and not scored_findings:
                score = 1
            if score > 0:
                scored_findings.append((score, self._format_finding(finding)))

        scored_findings.sort(key=lambda item: item[0], reverse=True)
        finding_sections = [section for _, section in scored_findings[:4]]

        report_sections: list[str] = []
        for report in project.reports[:2]:
            report_sections.append(
                f"Report: {report.title}\nSummary: {report.summary}\n"
                + "\n".join(
                    f"- {section.title}: {section.body}"
                    for section in report.sections[:2]
                )
            )

        combined = finding_sections + report_sections
        return "\n\n".join(combined[:6]).strip()

    @staticmethod
    def _format_finding(finding) -> str:
        evidence_lines = []
        for reference in finding.evidence[:3]:
            evidence_lines.append(
                f"- {reference.source_uri}: {reference.excerpt}"
            )
        joined_evidence = "\n".join(evidence_lines)
        return (
            f"Finding: {finding.title}\n"
            f"Severity: {finding.severity}\n"
            f"Summary: {finding.summary}\n"
            f"Recommendation: {finding.recommendation}\n"
            f"Evidence:\n{joined_evidence}"
        )
