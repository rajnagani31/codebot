class Animal: 
    def speak(self): 
        return 'Animal speaks' 

class Dog(Animal): 
    def speak(self): 
        return 'Dog barks' 

class Cat(Animal): 
    def speak(self): 
        return 'Cat meows' 

# Example usage: 
if __name__ == '__main__': 
    dog = Dog() 
    cat = Cat() 
    print(dog.speak())  # Output: Dog barks 
    print(cat.speak())  # Output: Cat meows
