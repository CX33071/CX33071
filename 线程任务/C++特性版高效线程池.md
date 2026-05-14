# C++特性版高效线程池

### 一、this指针

`this`是C++中非静态成员函数里的一个隐藏函数，它指向调用当前成员函数的那个对象本身：谁调用函数，`this`就指向谁

`this`是当前对象的地址，`*this`是当前对象本身，静态成员函数没有`this`指针

#### 用法：

##### 1.区分成员变量和函数形参

```c++
class Person {
private:
    int age;  // 成员变量
public:
    // 形参名和成员变量同名
    void setAge(int age) {
        // this->age 表示对象的成员变量
        // age 表示函数的形参
        this->age = age; 
    }
};
```

##### 2.链式调用，返回`*this`

让成员函数返回当前对象的引用，实现连续调用

```c++
class Person {
private:
    int age;
public:
    Person& setAge(int age) {
        this->age = age;
        return *this; // 返回当前对象本身
    }
    Person& showAge() {
        cout << "年龄：" << this->age << endl;
        return *this;
    }
};
int main() {
    Person p;
    // 链式调用
    p.setAge(25).showAge(); 
    return 0;
}
```

##### 3.在成员函数中获取对象地址

```c++
void printAddress() {
    cout << "当前对象地址：" << this << endl;
}
```

##### 4.委托构造

```c++
class Student {
public:
    string name;
    int age;
    // 主构造
    Student(string n, int a) : name(n), age(a) {}
    // 委托构造：复用上面的构造函数
    Student(string n) : this(n, 18) {} 
};
```

##### 5.模板类中显式指明依赖类作用域

模板派生类继承模板基类时，编译器找不到基类成员，要用`this->`显式告诉编译器是类成员

```c++
template<typename T>
class Base {
protected:
    int val = 100;
};
template<typename T>
class Derive : public Base<T> {
public:
    void show() {
        // 必须加 this->，否则编译报错
        cout << this->val << endl;
    }
};
```

`this`指向`Derive`,如果是自己的成员val,继承的基类也有val,那this->val如何区分是哪个类的val？

同名成员隐藏规则：`this->val` 默认优先找当前类自己的成员，隐藏掉基类的同名成员

```c++
// 加类名作用域：强制访问【基类】的val
    cout << Base<T>::val << endl; 
```

##### 6.` const this`

普通`this`指针：指针本身不可改指向，可以通过`this`修改对象成员

`const this`指针：不能通过`this`修改对象任何成员

```c++
class Person {
    int age;
public:
    void show() const {
        age = 20;   // 报错！const this 禁止修改成员
    }
};
```

`mutable`突破`const this`限制：用 `mutable` 修饰的成员，哪怕在 `const` 函数里也能改，`mutable`不受`const this`约束

#### `this`在多线程下是否安全？

多个线程访问同一个对象(有读有写)，会产生数据竞争

```c++
class Test {
    int num = 0;
public:
    void add() {
        this->num++;  // 多个线程同时执行这句 = 灾难
    }
};
```

怎么让`this`指向的对象变成线程安全？

给共享成员变量加锁：

```c++
#include <mutex>
class Test {
    int num = 0;
    mutex mtx;  // 锁
public:
    void add() {
        lock_guard<mutex> lock(mtx);  // 加锁
        this->num++;
    }
};
```



