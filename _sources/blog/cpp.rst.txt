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

Casting
-------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      cout << (int)3.14 << endl;
      cout << (double)3 / 2 << endl;

      return 0;
   }

Classes
-------

.. code-block:: cpp

   #include <iostream>
   #include <string>
   using namespace std;

   // Create the Book datatype
   class Book
   {
   public:
      string title;
      string author;

      void readBook()
      {
         cout << "Reading " + this->title + " by " + this->author << endl;
      }
   };

   int main()
   {
      // Construct the book1 object instance
      Book book1;
      book1.title = "Harry Potter";
      book1.author = "JK Rowling";

      // Print out info from the book1 object instance
      book1.readBook();
      cout << book1.title << endl;

      // Construct the book2 object instance
      Book book2;
      book2.title = "Lord of the Rings";
      book2.author = "JRR Tolkien";

      // Print out info from the book2 object instance
      book2.readBook();
      cout << book2.title << endl;

      return 0;
   }

Constants
---------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      const int BIRTH_YEAR = 1945;
      // BIRTH_YEAR = 1988; // Can't change BIRTH_YEAR
      cout << BIRTH_YEAR;

      return 0;
   }

Constructors
------------

.. code-block:: cpp

   #include <iostream>
   #include <string>
   using namespace std;

   // Create the Book datatype
   class Book
   {
   public:
      string title;
      string author;

      // Define the class' constuctor function
      // NOTE: This is like `def __init__()` in Python :D
      Book(string title, string author)
      {
         this->title = title;
         this->author = author;
      }

      void readBook()
      {
         cout << "Reading " + this->title + " by " + this->author << endl;
      }
   };

   int main()
   {
      // Construct the book1 object instance
      Book book1("Harry Potter", "JK Rowling");

      // Print out info from the book1 object instance
      book1.readBook();
      cout << book1.title << endl;

      // Construct the book2 object instance
      Book book2("Lord of the Rings", "JRR Tolkien");

      // Print out info from the book2 object instance
      book2.readBook();
      cout << book2.title << endl;

      return 0;
   }

