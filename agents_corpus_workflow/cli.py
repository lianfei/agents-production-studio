from __future__ import annotations

import argparse
import json
from pathlib import Path

from .api import serve
from .models import GenerationRequest, json_ready
from .service import WorkflowService


def _default_source_root() -> str:
    return str(Path.cwd())


def _default_output_dir() -> str:
    return str(Path.cwd() / "tmp")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agents-corpus", description="Analyze and generate AGENTS workflow artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--source-root", default=_default_source_root())
    shared.add_argument("--output-dir", default=_default_output_dir())
    shared.add_argument("--initial-batch-size", type=int, default=50)

    analyze = subparsers.add_parser("analyze-corpus", parents=[shared])
    analyze.add_argument("--max-files", type=int)

    schema = subparsers.add_parser("build-label-schema", parents=[shared])

    label = subparsers.add_parser("label-corpus", parents=[shared])
    label.add_argument("--max-files", type=int)

    review = subparsers.add_parser("review-labels", parents=[shared])
    review.add_argument("--max-files", type=int)

    generate = subparsers.add_parser("generate-agents", parents=[shared])
    generate.add_argument("--template-type", default="")
    generate.add_argument("--industry", required=True)
    generate.add_argument("--task-description", required=True)
    generate.add_argument("--target-user", default="general")
    generate.add_argument("--output-language", default="zh")
    generate.add_argument("--environment", default="")
    generate.add_argument("--constraint", action="append", default=[])
    generate.add_argument("--preferred-stack", action="append", default=[])
    generate.add_argument("--risk-tolerance", default="medium")
    generate.add_argument("--max-files", type=int)

    api = subparsers.add_parser("serve-api", parents=[shared])
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8765)
    api.add_argument("--enable-admin-endpoints", action="store_true")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    service = WorkflowService(args.source_root, args.output_dir, initial_batch_size=args.initial_batch_size)
    if args.command == "build-label-schema":
        path = service.build_schema()
        print(path)
        return
    if args.command == "analyze-corpus":
        result = service.analyze_corpus(max_files=args.max_files)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.command == "label-corpus":
        records, manifest_path = service.scan_corpus(max_files=args.max_files)
        profiles, labeled_path = service.label_corpus(records)
        print(
            json.dumps(
                {"manifest_path": str(manifest_path), "labeled_path": str(labeled_path), "count": len(profiles)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    if args.command == "review-labels":
        profiles = service.load_or_build_profiles(max_files=args.max_files)
        summary_path, review_path = service.review_labels(profiles)
        print(json.dumps({"summary_path": str(summary_path), "review_path": str(review_path)}, ensure_ascii=False, indent=2))
        return
    if args.command == "generate-agents":
        request = GenerationRequest(
            template_type=args.template_type,
            industry=args.industry,
            task_description=args.task_description,
            target_user=args.target_user,
            output_language=args.output_language,
            environment=args.environment,
            constraints=args.constraint,
            preferred_stack=args.preferred_stack,
            risk_tolerance=args.risk_tolerance,
        )
        response = service.generate_agents_document(request, max_files=args.max_files)
        print(json.dumps(json_ready(response), ensure_ascii=False, indent=2))
        return
    if args.command == "serve-api":
        serve(
            source_root=args.source_root,
            output_dir=args.output_dir,
            host=args.host,
            port=args.port,
            initial_batch_size=args.initial_batch_size,
            enable_admin_endpoints=args.enable_admin_endpoints,
        )
        return
    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
