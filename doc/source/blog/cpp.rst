GiraffeAcademy's C++ Examples
=============================

.. seealso::

   `C++ Programming | In One Video <https://youtu.be/raZSmcariyU>`_
      GiraffeAcademy's video.

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

Exceptions
----------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   double division(int a, int b)
   {
      if (b == 0)
      {
         throw "Division by zero error!";
      }
      return (a / b);
   }

   int main()
   {
      try
      {
         division(10, 0);
      }
      catch (const char *msg)
      {
         cerr << msg << endl;
      }

      return 0;
   }

For Loops
---------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      for (int i = 0; i < 5; i++)
      {
         cout << i << endl;
      }

      return 0;
   }

Functions
---------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   // Specify a method signature
   int addNumbers(int num1, int num2);

   int main()
   {
      // NOTE: We declare the function first
      int sum = addNumbers(4, 60);
      cout << sum << endl;

      return 0;
   }

   int addNumbers(int num1, int num2)
   {
      return num1 + num2;
   }

Getters & Setters
-----------------

.. code-block:: cpp

   #include <iostream>
   #include <string>
   using namespace std;

   // Create the Book datatype
   class Book
   {
   private:
      string title;
      string author;

   public:
      // Define the class' constuctor function
      // NOTE: This is like `def __init__()` in Python :D
      Book(string title, string author)
      {
         this->setTitle(title);
         this->setAuthor(author);
      }

      string getTitle()
      {
         return this->title;
      }

      void setTitle(string title)
      {
         this->title = title;
      }

      string getAuthor(string author)
      {
         return this->author;
      }

      void setAuthor(string author)
      {
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
      cout << book1.getTitle() << endl;

      // Construct the book2 object instance
      Book book2("Lord of the Rings", "JRR Tolkien");

      // Print out info from the book2 object instance
      book2.readBook();
      cout << book2.getTitle() << endl;

      return 0;
   }

If Statements
-------------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      // Define 2 booleans
      bool isStudent = false;
      bool isSmart = false;

      if (isStudent && isSmart)
      {
         cout << "You are a student" << endl;
      }
      else if (isStudent && !isSmart)
      {
         cout << "You are not a smart student" << endl;
      }
      else
      {
         cout << "You are not a student and not smart" << endl;
      }

      // >, <, >=, <=, !=, ==
      if (1 > 3)
      {
         cout << "Number comparison was true" << endl;
      }

      if ('a' > 'b')
      {
         cout << "Character comparison was true" << endl;
      }

      string myString = "cat";
      if (myString.compare("cat") != 0)
      {
         cout << "string comparison was true" << endl;
      }

      return 0;
   }

Inheritance
-----------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   // Create a Chef datatype
   class Chef
   {
   public:
      string name;
      int age;

      Chef(string name, int age)
      {
         this->name = name;
         this->age = age;
      }

      void makeChicken()
      {
         cout << "The chef makes chicken" << endl;
      }

      void makeSalad()
      {
         cout << "The chef makes salad" << endl;
      }

      void makeSpecialDish()
      {
         cout << "The chef makes a special dish" << endl;
      }
   };

   // Create an ItalianChef datatype that is an extenion of the Chef datatype
   class ItalianChef : public Chef
   {
   public:
      string countryOfOrigin;

      // Extended class' constructor from Chef's class constructor
      ItalianChef(string name, int age, string countryOfOrigin) : Chef(name, age)
      {
         this->countryOfOrigin = countryOfOrigin;
      }

      void makePasta()
      {
         cout << "The chef makes pasta" << endl;
      }

      // Override the Chef class' makeSpecialDish()
      void makeSpecialDish()
      {
         cout << "The chef makes chicken parmesan" << endl;
      }
   };

   int main()
   {
      // Example of the Chef class
      Chef myChef("Gordon Ramsay", 50);
      myChef.makeSpecialDish();

      // Example of the extended ItalianChef class
      ItalianChef myItalianChef("Massimo Bottura", 55, "Italy");
      myItalianChef.makeSpecialDish();
      cout << myItalianChef.age << endl;

      return 0;
   }

Numbers
-------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      cout << 2 * 3 << endl; // Basic arithmetic: +, -, /, *
      cout << 10 % 3 << endl; // Modulus operator: returns the remainder of 10 / 3
      cout << (1 + 2) * 3 << endl; // Order of operations

      /*
         Division rules with ints and doubles:
            f/f = f
            i/i = i
            i/f = f
            f/i = f
      */
      cout << 10 / 3.0 << endl;

      int num = 10;
      num += 100; // +=, -=, /=, *=
      cout << num << endl;

      // Example: variable incrementation
      num++;
      cout << num << endl;

      return 0;
   }

Pointers
--------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      /*
         What pointers are:
         - Exposes memory addresses
         - Manipulates memory addresses
         Why we use pointers:
         - Memory addresses can change per-system
         - Directly change data without copying it
      */

      // Print out an integer variable's memory address
      int num = 10;
      cout << &num << endl;

      // Store the integer variable's memory address into memory
      int *pNum = &num;
      cout << pNum << endl; // Print the memory adddress
      cout << *pNum << endl; // Dereference the memory address to fetch its stored value

      return 0;
   }

Printing
--------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      cout << "Hello World!" << endl;

      return 0;
   }

Strings 
-------

.. code-block:: cpp

   #include <iostream>
   #include <string>
   using namespace std;

   int main()
   {
      string greetings = "Hello";
      //    char indexes: 01234

      cout << greetings.length() << endl; // Get string length
      cout << greetings[0] << endl; // Get 1st character of string
      cout << greetings.find("llo") << endl; // Find "llo"'s starting character position
      cout << greetings.substr(2) << endl; // Get all characters, starting from the 2nd character of the string
      cout << greetings.substr(1, 3) << endl; // Get 3 characters, starting from the 1st character of the string

      return 0;
   }

Switch Statements
-----------------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      char myGrade = 'A';
      switch (myGrade)
      {
         case 'A':
               cout << "You pass" << endl;
               break;
         case 'B':
               cout << "You fail" << endl;
               break;
         default:
               cout << "Invalid grade" << endl;
      }

      return 0;
   }

User Input
----------

.. code-block:: cpp

   #include <iostream>
   #include <string>
   using namespace std;

   int main()
   {
      string name;
      cout << "Enter your name: ";
      cin >> name;
      cout << "Hello " << name << endl;

      int num1, num2;
      cout << "Enter first number: ";
      cin >> num1;
      cout << "Enter second number: ";
      cin >> num2;
      cout << "Answer: " << num1 + num2 << endl;

      return 0;
   }

Variables
---------

.. code-block:: cpp

   #include <iostream>
   #include <string>
   using namespace std;

   int main()
   {
      /*
         Traits:
         - Case-sensitive
         - May begin with letters
         - Can include letters, numbers, or _
        Convention:
         - First word lower-case, rest upper-case (camelCase)
         - Example: myVariable
      */

      string name = "Mike"; // string of characters, not primitive
      char testGrade = 'A'; // single 8-bit character

      // NOTE: You can make them unsigned by adding the "unsigned" prefix
      short age0 = 10; // atleast 16-bit signed integer
      int age1 = 20; // atleast 16-bits signed integer (not smaller than short)
      long age2 = 30; // atleast 32-bits signed integer
      long long age3 = 40; // atleast 64-bits signed integer

      float gpa0 = 2.5f; // single percision floating point
      double gpa1 = 3.5l; // double-precision floating point
      long double gpa2 = 3.5; // extended-precision floating point

      bool isTall; // 1-bit -> true/false
      isTall = true;

      return 0;
   }

Vectors
-------

.. code-block:: cpp

   #include <iostream>
   #include <string>
   #include <vector>
   using namespace std;

   int main()
   {
      // Define a vector of strings
      vector<string> friends;
      // Append 3 strings into the vector
      friends.push_back("Oscar");
      friends.push_back("Angela");
      friends.push_back("Kevin");
      // Append "Jim" at the 2nd index of the vendor
      friends.insert(friends.begin() + 1, "Jim");

      // Print out the friend vector's first 3 members
      cout << friends.at(0) << endl;
      cout << friends.at(1) << endl;
      cout << friends.at(2) << endl;
      // Print out the friend vector's size
      cout << friends.size() << endl;

      return 0;
   }

While Loops
-----------

.. code-block:: cpp

   #include <iostream>
   using namespace std;

   int main()
   {
      // Notify that this is a while loop
      cout << "Executing while loop" << endl;

      // Do while loop
      int index = 1;
      while (index <= 5)
      {
         cout << index << endl;
         index++;
      }

      // Notify that this is a do-while loop
      cout << "Executing do-while loop" << endl;

      do
      {
         cout << index << endl;
         index++;
      } while (index <= 5);

      return 0;
   }
