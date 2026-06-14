
Hardware Auto Exposure on the GPU
=================================

Automatic Exposure
------------------

Automatic exposure adjusts the sensitivity to light to maintain an appropriate brightness level in a scene, regardless of changing lighting conditions. This process ensures that details in both dark shadows and bright highlights are preserved.

Principles of Auto Exposure
---------------------------

The system dynamically modulates sensitivity based on ambient light levels. In low-luminance environments, sensitivity is increased to accumulate sufficient light. In high-luminance environments, sensitivity is reduced to prevent overexposure and preserve detail in bright regions.

Scene Luminance and Key
-----------------------

To implement automatic exposure, the average luminance of a scene must be determined. This value is often called the scene's "key." A scene with high average luminance is considered "high key," while a dark scene is "low key."

The average luminance :math:`\bar{L}_w` can be calculated using the following formula:

.. math::

   \bar{L}_w = \frac{1}{N} \exp\left(\sum_{x,y} \log(\epsilon + L_w(x,y))\right)

The exposure is then determined by the following formulas:

.. math::

   EV_{100} = \log_2\left(\frac{\bar{L} \cdot 100}{12.5}\right)

.. math::

   \text{Exposure} = \frac{1}{1.2 \cdot 2^{EV_{100}}}

Optimized Implementation
------------------------

Traditional automatic exposure methods often require multiple textures to store intermediate values, such as the previous average luminance and the current average luminance calculation.

The implementation presented here optimizes this process by using a single texture to hold both the previous and current brightness information, thereby reducing memory bandwidth and texture fetches.

.. list-table::

   :header-rows: 1
   :stub-columns: 1

   * -
     - Traditional Method
     - Optimized Method
   * - Temporary Images Required
     - * One texture for previous average luminance.
       * One texture for current average luminance.
     - * One texture for combined brightness information.
   * - Processing Steps
     - #. Store the previous average luminance.
       #. Calculate the current average luminance.
       #. Combine and smooth averages to determine exposure.
     - #. Calculate and smooth the average luminance in a single pass.
       #. Apply the smoothed average to determine exposure.

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
