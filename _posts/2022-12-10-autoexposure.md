---
layout: post
title: "Using Hardware Blending to Smooth Auto-Exposure"
---

Some graphics pipelines use 2 textures and 3 passes for auto-exposure. 1 pass to store previous average brightness, 1 pass to generate current average brightness, and 1 pass for temporally smooth average brightnesses and calculate auto-exposure.

We can use the GPU’s blending hardware to generate and temporally smooth the screen’s average brightness in 1 pass. Afterward, we use the second pass to calculate auto-exposure.

