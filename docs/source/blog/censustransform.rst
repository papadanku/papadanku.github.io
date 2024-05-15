
Census Transform in HLSL
========================

The census transform is a filter that represents the pixel's neighborhood relationship in a binary string. The binary string will be ``0000000`` if the center pixel is lesser than all of its neighbors. The binary string will be ``11111111`` if the center pixel is greater than or equal to all of its neighbors.

The filter does not depend on the image's actual intensity. As a result, the filter is robust to illumination.

Source Code
-----------

.. code::

   float GetGreyScale(float3 Color)
   {
      return max(max(Color.r, Color.g), Color.b);
   }

   float GetCensusTransform(sampler SampleImage, float2 Tex, float2 PixelSize)
   {
      float OutputColor = 0.0;
      float4 ColumnTex[3];
      ColumnTex[0] = Tex.xyyy + (float4(-1.0, +1.0, 0.0, -1.0) * PixelSize.xyyy);
      ColumnTex[1] = Tex.xyyy + (float4( 0.0, +1.0, 0.0, -1.0) * PixelSize.xyyy);
      ColumnTex[2] = Tex.xyyy + (float4(+1.0, +1.0, 0.0, -1.0) * PixelSize.xyyy);
      
      const int Neighbors = 8;
      float SampleNeighbor[Neighbors];
      SampleNeighbor[0] = GetGreyScale(tex2D(SampleImage, ColumnTex[0].xy).rgb);
      SampleNeighbor[1] = GetGreyScale(tex2D(SampleImage, ColumnTex[1].xy).rgb);
      SampleNeighbor[2] = GetGreyScale(tex2D(SampleImage, ColumnTex[2].xy).rgb);
      SampleNeighbor[3] = GetGreyScale(tex2D(SampleImage, ColumnTex[0].xz).rgb);
      SampleNeighbor[4] = GetGreyScale(tex2D(SampleImage, ColumnTex[2].xz).rgb);
      SampleNeighbor[5] = GetGreyScale(tex2D(SampleImage, ColumnTex[0].xw).rgb);
      SampleNeighbor[6] = GetGreyScale(tex2D(SampleImage, ColumnTex[1].xw).rgb);
      SampleNeighbor[7] = GetGreyScale(tex2D(SampleImage, ColumnTex[2].xw).rgb);
      float CenterSample = GetGreyScale(tex2D(SampleImage, ColumnTex[1].xz).rgb);

      // Generate 8-bit integer from the 8-pixel neighborhood
      for(int i = 0; i < Neighbors; i++)
      {
         float Comparison = step(SampleNeighbor[i], CenterSample);
         OutputColor += ldexp(Comparison, i);
      }

      // Convert the 8-bit integer to float, and average the results from each channel
      return OutputColor * (1.0 / (exp2(8) - 1));
   }
