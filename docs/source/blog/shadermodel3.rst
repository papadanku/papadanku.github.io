
Project Reality: Shader Model 3.0 Considerations
================================================

`The Project Reality Team <https://www.realitymod.com/>`_ updated Project Reality to support Shader Model 3. The update gave Project Reality more graphical potential. This post considerations when porting shaders from Shader Model 2 to 3.

Fogging
-------

From Shader Model 3, fogging is no longer fixed-function. You must implement your fogging method in the pixel shader.

Output Register Count
---------------------

- `Shader Model 2 vertex shaders have a certain number of output registers for each type of data <https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx9-graphics-reference-asm-vs-registers-vs-2-x>`__.

   :oPos: 1 position
   :oFog: 1 fog
   :oPts: 1 point-size
   :oD#: 2 vertex color
   :oT#: 8 texture coordinate

- In Shader Model 3, you have 12 output registers available for any type of data.

Input Register Format
---------------------

- In Shader Model 2, output registers have different levels of precision.

   For example, `vertex color registers, like oD#, are 8 bits of unsigned data, in the range of 0-1 in the pixel shader <https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx9-graphics-reference-asm-ps-registers-input-color>`_.

- When you port vertex colors ``oD#`` from Shader Model 2 to 3, you must apply ``saturate()`` to the vertex color output.

Register Assignments and Declarations
-------------------------------------

If you are hit with the following asm, with constants not declared in ASM.

.. code-block::

    VertexShader = asm
    {
        vs.1.1

        dcl_position0 v0

        add r0.xyz, v0.xzw, -c[0].xyz
        mul r0.xyz, r0.xyz, c[1].xyw // z = 0, w = 1
        add oPos.x, r0.x, -c[1].w
        add oPos.y, r0.y, -c[1].w
        mov oPos.z, r0.z
        mov oPos.w, c[1].w // z = 0, w = 1
        add r1, v0.y, -c[2].x
        mul oD0, r1, c[2].y
        mov oD0.a, c[1].z // z = 0
    };

    PixelShader = asm
    {
        ps.1.1
        mov r0, v0
    };

To solve this problem, we use the ``: register()`` to a shader variable to a particular register. You can read more about it `here <https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-variable-register>`.

.. code-block::

    // Assign variables to registers because DICE didn't do so in their ASM.
    float4 Constant0 : register(c0); // c[0]
    float4 Constant1 : register(c1); // c[1]
    float4 Constant2 : register(c2); // c[2]

    struct APP2PS_ProjectRoad
    {
        float4 Pos : POSITION0;
    };

    struct VS2PS_ProjectRoad
    {
        float4 HPos : POSITION;
        float4 Color : TEXCOORD0;
    };

    VS2PS_ProjectRoad VS_ProjectRoad(APP2PS_ProjectRoad Input)
    {
        VS2PS_ProjectRoad Output = (VS2PS_ProjectRoad)0.0;

        // add r0.xyz, v0.xzw, -c[0].xyz
        // mul r0.xyz, r0.xyz, c[1].xyw // z = 0, w = 1
        float3 ProjPos = Input.Pos.xzw - Constant0.xyz;
        ProjPos *= Constant1.xyw; // z = 0, w = 1

        // add oPos.x, r0.x, -c[1].w
        // add oPos.y, r0.y, -c[1].w
        // mov oPos.z, r0.z
        // mov oPos.w, c[1].w // z = 0, w = 1
        Output.HPos.x = ProjPos.x - Constant1.w;
        Output.HPos.y = ProjPos.y - Constant1.w;
        Output.HPos.z = ProjPos.z;
        Output.HPos.w = Constant1.w; // z = 0, w = 1

        // add r1, v0.y, -c[2].x
        // mul oD0, r1, c[2].y
        // mov oD0.a, c[1].z // z = 0
        float4 Color = Input.Pos.y - Constant2.x;
        Output.Color = Color * Constant2.y;
        Output.Color.a = Constant1.z; // z = 0
        Output.Color = saturate(Output.Color);

        return Output;
    }
