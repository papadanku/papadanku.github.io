
A Refresher on Coordinate Spaces
================================

Standard Basis
--------------

Defines the directions of the x-axis, y-axis, and z-axis.

:(1.0, 0.0, 0.0): x-axis
:(0.0, 1.0, 0.0): y-axis
:(0.0, 0.0, 1.0): z-axis

.. list-table:: Coordinate Spaces Overview
   :header-rows: 1

   * - Coordinate Space
     - Standard-Basis Location
     - (0.0, 0.0, 0.0) Location
   * - Tangent-Space
     - On the **face or vertex**.
     - On the center of the **face or vertex**.
   * - Object-Space
     - On the **object**.
     - On the center of the **object**.
   * - World-Space
     - On the **world**.
     - On the center of the **world**.
   * - View-Space
     - On the **viewer**.
     - On the center of the **viewer**.

Tangent Space
-------------

Tangent space is a local coordinate system defined on the surface of a mesh. It is essential for techniques like normal mapping, where lighting calculations occur relative to the surface normal rather than the object's orientation.

The basis for tangent space is defined by three vectors:

- **Normal** :math:`$\mathbf{N}$`: Perpendicular to the surface.
- **Tangent** :math:`$\mathbf{T}$`: Parallel to the surface.
- **Bitangent** :math:`$\mathbf{B}$`: Perpendicular to both the normal and the tangent.

The transformation from Tangent Space to World Space uses the **TBN Matrix** (Tangent, Bitangent, Normal):

.. math::

   \mathbf{P}_{\text{world}} = \mathbf{M}_{\text{TBN}} \times \mathbf{P}_{\text{tangent}}

Object Space
------------

Object space, also known as local space, defines coordinates relative to a specific 3D model. The origin $(0, 0, 0)$ typically corresponds to the center or base of the model. These coordinates remain constant regardless of the model's position, rotation, or scale in the scene.


World Space
-----------

World space provides a global reference frame for all objects in a scene. Every object is placed within this single, unified coordinate system.

The transformation from Object Space to World Space uses the **Model Matrix**:

.. math::

   \mathbf{P}_{\text{world}} = \mathbf{M}_{\text{model}} \times \mathbf{P}_{\text{object}}

View Space
----------

View space, or eye space, defines coordinates from the perspective of the camera. In this space, the camera sits at the origin $(0, 0, 0)$ and typically looks down a specific axis, such as the negative z-axis.

The transformation from World Space to View Space uses the **View Matrix**:

.. math::

   \mathbf{P}_{\text{view}} = \mathbf{M}_{\text{view}} \times \mathbf{P}_{\text{world}}
