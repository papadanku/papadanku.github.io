
Hardware Auto Exposure on The GPU
=================================

Understanding Auto Exposure
---------------------------

Have you ever noticed how your camera or eyes adjust when you move between very bright and very dark places? That's auto exposure!

Let's try a couple of experiments:

**Experiment 1: Indoors to Outdoors**

#. Grab your phone or a camera.
#. Find a spot where part of the scene is very dark \(like a shadow\) and another part is very bright \(like direct sunlight\).
#. If your camera has "auto exposure" mode, make sure it's on.
#. First, point your camera at the dark spot. Notice how the picture looks.
#. Now, slowly turn your camera towards the bright spot. See how the image changes?

**Experiment 2: Dark Room to Bright Outdoors**

1. Go into a very dark room, but make sure it's bright outside the window or door.
2. Stay in the dark room for a few minutes to let your eyes adjust.
3. Now, slowly walk outside into the bright light.

What you probably noticed in both experiments is this:

* When you \(or your camera\) are in a **dark place**, you become **more sensitive to light**, trying to gather as much as possible to see.
* When you \(or your camera\) are in a **bright place**, you become **less sensitive to light**, preventing everything from looking washed out.

**This is the main goal of auto exposure:** to automatically change how sensitive we are to light, depending on how bright our surroundings are. It helps us see details in both dark shadows and bright highlights.

How We Measure a Scene's Brightness
-----------------------------------

In auto exposure, we need a way to describe how "bright" a scene truly is. We call this the scene's "Key." A very bright scene has a "high key," while a dark scene has a "low key."

We can figure out this "key" by calculating the average brightness of all the pixels in the scene. A common way to do this is with this formula:

.. math::

   \bar{L}_w = \frac{1}{N} \exp\left(\sum_{x,y} \log(\epsilon + L_w(x,y))\right)

.. note::

   *Don't worry too much about the complex math!* This formula essentially helps us find a good "average" brightness for the entire picture, which tells us the scene's "key."

Making Auto Exposure Faster
---------------------------

Normally, when computers calculate auto exposure for graphics or photos, it can involve several steps and temporary images \(called "textures"\).

My new method simplifies this process, using fewer steps and just one main temporary image. Here's a quick comparison:

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * -
     - Typical Auto Exposure Method
     - My Auto Exposure Method
   * - Temporary Images Needed
     - * One image to remember the *previous* average brightness.
       * Another image to calculate the *current* average brightness.
     - * Just **one** image that holds both the previous and current brightness information.
   * - Processing Steps
     - #. Save the previous average brightness.
       #. Calculate the current average brightness.
       #. Combine and smooth these averages to figure out the best exposure.
     - #. Calculate and smooth the average brightness in one go.
       #. Use that smoothed average to figure out the best exposure.

Source Code
-----------

.. code-block:: hlsl

   /*
      Automatic exposure shader using hardware blending.
   */

   /*
      Vertex shaders.
   */

   struct APP2VS
   {
      float4 HPos : POSITION;
      float2 Tex0 : TEXCOORD0;
   };

   struct VS2PS
   {
      float4 HPos : POSITION;
      float2 Tex0 : TEXCOORD0;
   };

   VS2PS VS_Quad(APP2VS Input)
   {
      VS2PS Output;
      Output.HPos = Input.HPos;
      Output.Tex0 = Input.Tex0;
      return Output;
   }

   /*
      AutoExposure(): https://knarkowicz.wordpress.com/2016/01/09/automatic-exposure/
   */

   float3 GetAutoExposure(float3 Color, float2 Tex)
   {
      float LumaAverage = exp(tex2Dlod(SampleLumaTex, float4(Tex, 0.0, 99.0)).r);
      float Ev100 = log2(LumaAverage * 100.0 / 12.5);
      Ev100 -= _ManualBias; // Optional manual bias.
      float Exposure = 1.0 / (1.2 * exp2(Ev100));
      return Color * Exposure;
   }

   float4 PS_GenerateAverageLuma(VS2PS Input) : COLOR0
   {
      float4 Color = tex2D(SampleColorTex, Input.Tex0);
      float3 Luma = max(Color.r, max(Color.g, Color.b));

      // OutputColor0.rgb = Highest brightness from red/green/blue components.
      // OutputColor0.a = Weight for temporal blending.
      float Delay = 1e-3 * _Frametime;
      return float4(log(max(Luma.rgb, 1e-2)), saturate(Delay * _SmoothingSpeed));
   }

   float3 PS_Exposure(VS2PS Input) : COLOR0
   {
      float4 Color = tex2D(SampleColorTex, Input.Tex0);
      return GetAutoExposure(Color.rgb, Input.Tex0);
   }

   technique AutoExposure
   {
      // Pass0: Renders to a self-blending texture.
      // NOTE: Ensure no other shader overwrites this texture.
      pass GenerateAverageLuma
      {
         // Enable hardware blending.
         BlendEnable = TRUE;
         BlendOp = ADD;
         SrcBlend = SRCALPHA;
         DestBlend = INVSRCALPHA;

         VertexShader = VS_Quad;
         PixelShader = PS_GenerateAverageLuma;
      }

      // Pass1: Applies Auto Exposure using the texture from Pass0.
      pass ApplyAutoExposure
      {
         VertexShader = VS_Quad;
         PixelShader = PS_Exposure;
      }
   }

References
----------

Reinhard, E., Stark, M., Shirley, P., & Ferwerda, J. \(2002\). Photographic tone reproduction for digital images. ACM Transactions on Graphics, 21\(3\), 267-276. https://doi.org/10.1145/566654.566575
