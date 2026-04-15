# Filling Guide (English)

This guide explains what to enter at each step and what makes an input set strong.

## 1. Think in four parts

Good inputs usually make these four things explicit:

- what you want to build
- where it will run
- what constraints cannot be violated
- what success looks like

## 2. Step-by-step

### Step 1: Template and Goal

- At the top of this step, you can load a built-in sample from `examples/form_inputs` or import a local JSON file to prefill the form.
- Common reusable fields are `template_type`, `industry`, `task_description`, `target_user`, `output_language`, `environment`, `preferred_stack`, `constraints`, `creative_notes`, and `risk_tolerance`.
- Choose the template that matches the delivery shape.
- Industry should describe the business domain, not the tech stack.
- Task description is the most important field. State the final deliverable, target users, usage mode, and success direction.

### Step 2: Scenario and Environment

- Target user: who will actually use the result
- Output language: the primary language of the generated AGENTS.md
- Environment: use combinations such as `browser + HTTP service + Docker`
- Risk tolerance: choose low for production-sensitive work

### Step 3: Preferences and Constraints

- Preferred stack: what you would like to use
- Constraints: rules that cannot be violated
- Creative notes: style, tone, or business-facing presentation requirements

### Step 4: Supplemental Q&A

This step is for missing critical details, not for rewriting the whole request.

### Step 5: PLAN Preview

Review PLAN.md before generating the final AGENTS.md. If the plan is off, go back and refine the earlier inputs.

## 3. Example quality

A good sample:

- clearly states the final artifact
- uses combined environment choices
- includes concrete constraints

An excellent sample:

- also clarifies deployment expectations
- explains acceptance and UI/result behavior
- defines visibility and information-exposure boundaries

## 4. Sample files

- [`../examples/form_inputs/good_sample.zh-CN.json`](../examples/form_inputs/good_sample.zh-CN.json)
- [`../examples/form_inputs/excellent_sample.zh-CN.json`](../examples/form_inputs/excellent_sample.zh-CN.json)
