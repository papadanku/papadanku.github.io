GiraffeAcademy's C++ Examples
=============================

Abstract Classes
----------------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   class Vehicle
   {
   public:
      virtual void move() = 0;
      void getDescription()
      {
         cout << "Vehicles are used for transportation" << endl;
      }
   };

   class Bicycle : public Vehicle
   {
   public:
      void move()
      {
         cout << "The bicycle pedals forward" << endl;
      }
   };

   class Plane : public Vehicle
   {
   public:
      virtual void move()
      {
         cout << "The plane flys through the sky" << endl;
      }
   };

   int main()
   {
      Plane myPlane;
      myPlane.move();
      myPlane.getDescription();

      return 0;
   }

Arrays
------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      // Define an integer array
      // int luckyNumbers[6];
      int luckyNumbers[] = {4, 8, 15, 16, 23, 42};
      // indexes:           0  1   2   3   4   5

      // Set the number 99 at the 1st member
      luckyNumbers[0] = 90;

      // Print out the array's 1st and 2nd members
      cout << luckyNumbers[0] << endl;
      cout << luckyNumbers[1] << endl;

      return 0;
   }

Arrays (2D)
-----------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      // Define a 2D integer array
      // int numberGrid[2][3];
      int numberGrid[2][3] = {{1, 2, 3}, {4, 5, 6}};

      // Set the number 99 at [row 1][column 2]
      numberGrid[0][1] = 99;

      // Print [row 1][column 1 and 2]
      cout << numberGrid[0][0] << endl;
      cout << numberGrid[0][1] << endl;

      return 0;
   }

