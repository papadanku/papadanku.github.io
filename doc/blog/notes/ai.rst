
How I Used AI for Project Reality Development
=============================================

The Question
-------------

How can a single developer simultaneously create, maintain, and modernize documentation, shaders, and .NET build scripts?

The Methods
------------

For RealityDocs, agentic AI serves as a technical writer. It streamlines documentation migration by porting legacy content from various wiki markup languages into structured reStructuredText while preserving headers, lists, and links. The AI also revises existing documentation to improve clarity. It transforms dense, inconsistent, or jargon-heavy text into consistent Plain English, making it accessible for global readers. Additionally, the AI assists in documenting previously undocumented code by analyzing source files and generating accurate docstrings that explain a function's purpose, parameters, and return values.

For RealityShaders, in-game Python, and .NET build scripts, agentic AI acts as an analyzer, boilerplate generator, and consultant. AI helps with codebase analysis by identifying patterns and dependencies within large, undocumented files, enabling a better understanding of legacy logic. The AI also suggests performance optimizations. For example, it can analyze a shader implementation and recommend more efficient mathematical operations or instructions to improve GPU performance. Finally, the AI acts as a boilerplate generator, producing repetitive or conceptual code structures.

The Solution
------------

The solution is to offload predictive, high-volume tasks to AI. I act as the "human in the loop," overseeing and revising the output to ensure correctness.

Tools Used
-----------

The following tools are utilized in this workflow:

- AI Agent: `opencode <https://opencode.ai>`_
- AI Skills: `RealitySkills <https://gitlab.com/realitymod/public/realityskills>`_
- API Key: `Google AI Studio <https://aistudio.google.com/>`_
- Models: Gemma 4 31B IT (Planning) and Gemma 4 26B A4B IT (Execution)
