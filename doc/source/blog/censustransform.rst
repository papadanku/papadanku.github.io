
Census Transform on The GPU
===========================

The Census Transform encodes a pixel's neighborhood relationships into a binary string. A binary string of "00000000" indicates the center pixel is less than all neighbors, while "11111111" means it's greater than or equal to all neighbors.

This transform is robust to illumination changes as it relies on relative pixel intensities, not absolute values.

.. code-block:: none
   :caption: Source Code

   float GetGreyScale(float3 Color)
   {
      return max(max(Color.r, Color.g), Color.b);
   }

   float GetCensusTransform(sampler SampleImage, float2 Tex, float2 PixelSize)
   {
      float OutputColor = 0.0;
      float4 ColumnTex[3];
      ColumnTex[0] = Tex.xyyy + float4(-1.0, 1.0, 0.0, -1.0) * PixelSize.xyyy;
      ColumnTex[1] = Tex.xyyy + float4(0.0, 1.0, 0.0, -1.0) * PixelSize.xyyy;
      ColumnTex[2] = Tex.xyyy + float4(1.0, 1.0, 0.0, -1.0) * PixelSize.xyyy;

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

      // Generate 8-bit integer from the 8-pixel neighborhood.
      for (int i = 0; i < Neighbors; i++)
      {
         float Comparison = step(SampleNeighbor[i], CenterSample);
         OutputColor += ldexp(Comparison, i);
      }

      // Normalize the 8-bit integer to a float.
      return OutputColor / 255.0; // 2^8 - 1 = 255
   }
