from services.api.app.domain.repository import SeedRepository
from services.api.app.services.orchestration import AssessmentOrchestrator


def test_local_intake_creates_project_with_founder_friendly_guidance() -> None:
    orchestrator = AssessmentOrchestrator(SeedRepository())

    project = orchestrator.create_project(
        name="Founder-first migration",
        client_name="Founders Inc",
        source_kind="local_directory",
        source_target="demo-systems/legacycart",
        expected_users=20,
        preferred_cloud="aws",
        business_constraints=["Keep ops lean"],
        compliance_notes=["PII"],
        credential_label="Local folder",
        credential_kind="none",
    )

    intake = orchestrator.get_intake_profile(project.id)
    deployment = orchestrator.get_deployment_plan(project.id)
    bundle = orchestrator.build_assessment(project.id)

    assert intake.expected_users == 20
    assert bundle.run.pipeline_summaries[0].pipeline_key == "intake_clarification"
    assert any(agent.agent_key == "hosting_fit_advisor" for agent in bundle.run.agent_outputs)
    assert deployment.recommended_platform.platform_key == "aws-ec2"
    assert "plain language" in deployment.founder_summary.lower()


def test_deployment_plan_prefers_simpler_targets_for_small_traffic() -> None:
    orchestrator = AssessmentOrchestrator(SeedRepository())
    project = orchestrator.create_project(
        name="Simple frontend",
        client_name="Studio",
        source_kind="github",
        source_target="https://github.com/example/simple-frontend",
        expected_users=15,
        preferred_cloud="aws",
        business_constraints=[],
        compliance_notes=[],
        credential_label="GitHub token",
        credential_kind="token",
    )

    deployment = orchestrator.get_deployment_plan(project.id)

    platform_keys = [option.platform_key for option in deployment.platform_options]
    assert platform_keys[:3] == ["vercel", "railway", "aws-ec2"]
    assert deployment.recommended_platform.platform_key == "vercel"
