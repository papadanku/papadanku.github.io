
How I Used AI for Project Reality Development
=============================================

As part of the Project Reality Team, I create, maintain, and modernize documentation, shaders, and .NET build scripts. These tasks require repetitive, high-volume technical work.

In this post, I use the Q.M.S. (Question, Method, Solution) process, which my 8th-grade mathematics teacher taught me to approach a problem.

Question
--------

How do we offload and automate tasks that require tedious, high-volume digital work?

Method
------

It is the current year, and AI agents are now available from Anthropic [1]_, Google [2]_, Mistral AI [3]_, and the open-source community [4]_. For accessibility, I choose *opencode*.

For RealityDocs [5]_, the *opencode* agent serves as my technical writer (sorry *[R-DEV] PotatoLord*!). It uses the RealitySkills `restructuredtext-writer` skill [7]_ to maintain consistency. I use it to migrate documentation, porting forum posts written in a wiki markup language to reStructuredText while preserving headers, lists, and links. It also revises existing documentation to improve clarity. It transforms dense, inconsistent, or jargon-heavy text into consistent Plain English, making it accessible for our global readers. Additionally, the AI assists in documenting previously undocumented code by analyzing source files and generating accurate docstrings and other documentation that explain a function's purpose, parameters, and return values.

For RealityShaders [6]_, RealityUDL [8]_, in-game Python, and .NET build scripts, I use AI as an analyzer, boilerplate generator, and "consultant". As an analyzer, AI helps with codebase analysis by identifying patterns and dependencies within large, undocumented files. As a "consultant", it also suggests performance optimizations. For example, it can analyze a shader implementation and recommend more efficient mathematical operations or instructions. As a boilerplate generator, it produces repetitive or conceptual code structures.

Solution
--------

The solution is to The solution is to offload predictive, high-volume technical tasks to an AI agent. I act as the "human in the loop," overseeing and revising the output to ensure correctness. predictive, high-volume tasks to an AI agent. I act as the "human in the loop," overseeing and revising the output to ensure correctness.

Tools Used
-----------

The following tools are utilized in this workflow:

- AI Agent: `opencode <https://opencode.ai>`_
- API Key: `Google AI Studio <https://aistudio.google.com/>`_
- Models: Gemma 4 31B IT (Planning) and Gemma 4 26B A4B IT (Execution)

----

.. [#] https://claude.com/product/claude-code
.. [#] https://antigravity.google/product/antigravity-cli
.. [#] https://mistral.ai/products/vibe/
.. [#] https://opencode.ai/
.. [#] https://gitlab.com/realitymod/public/RealityDocs
.. [#] https://github.com/realitymod/RealityShaders
.. [#] https://gitlab.com/realitymod/public/realityskills
.. [#] https://gitlab.com/realitymod/public/realityudl
