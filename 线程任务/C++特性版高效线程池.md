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

### 二、`std::function`

##### 作用：把一切可调用对象(函数，`lambda`，仿函数，绑定器)统一包装成同一种类型，方便存储传递回调，是万能函数包装器，可以理解成一个函数指针

##### 语法：

```c++
// 格式
std::function<返回值(参数列表)> 变量名;
// 例子：包装一个返回int、参数是int,int的可调用对象
std::function<int(int, int)> func;
```

##### 示例：

1.包装普通函数：

```c++
#include <iostream>
#include <functional>
using namespace std;
int add(int a, int b) { return a + b; }
int main() {
    function<int(int, int)> f = add;
    cout << f(2, 3) << endl;  // 输出 5
}
```

2.包装`lambda`

```c++
function<int(int, int)> f = [](int a, int b) {
    return a * b;
};
cout << f(2, 3);  // 6
```

3.配合`bind`包装成员函数

```c++
Test t;
function<int(int)> f = bind(&Test::show, &t, placeholders::_1);
cout << f(5);  // 50
```

##### 用途：

1.实现回调函数

```c++
void run(function<void()> callback) {//参数是可调用对象
    callback();  // 调用回调
}
int main() {
    run([]() { cout << "回调执行\n"; });
}
```

2.把不同可调用对象存入同一容器

```c++
vector<function<int(int, int)>> vec;
vec.push_back(add);
vec.push_back([](int a,int b){return a-b;});
```

3.实现状态机、策略模式、事件分发

状态机：

```c++
#include <iostream>
#include <functional>
using namespace std;
// 状态枚举
enum State { IDLE, RUN, STOP };
class StateMachine {
public:
    // 当前状态执行函数
    function<void()> curState;
    // 切换状态
    void switchState(State s) {
        switch (s) {
            case IDLE: curState = [this](){ idle(); }; break;
            case RUN:  curState = [this](){ run(); };  break;
            case STOP: curState = [this](){ stop(); }; break;
        }
    }
    // 每一帧执行当前状态
    void update() {
        if(curState) curState();
    }
private:
    void idle()  { cout << "空闲状态\n"; }
    void run()   { cout << "运行状态\n"; }
    void stop()  { cout << "停止状态\n"; }
};
int main() {
    StateMachine sm;
    sm.switchState(IDLE);
    sm.update();
    sm.switchState(RUN);
    sm.update();
    sm.switchState(STOP);
    sm.update();
    return 0;
}
```

事件分发：

```c++
#include <iostream>
#include <functional>
#include <vector>
#include <unordered_map>
using namespace std;
// 事件分发器
class EventDispatcher {
public:
    // 事件回调：携带int参数
    using EventCb = function<void(int)>;
    unordered_map<int, vector<EventCb>> eventMap;
    // 绑定事件
    void on(int eventId, EventCb cb) {
        eventMap[eventId].push_back(cb);
    }
    // 触发事件
    void emit(int eventId, int msg) {
        if(!eventMap.count(eventId)) return;
        for(auto &cb : eventMap[eventId]) {
            cb(msg);
        }
    }
};
int main() {
    EventDispatcher ed;
    // 绑定事件1001
    ed.on(1001, [](int val){
        cout << "模块A收到：" << val << endl;
    });
    ed.on(1001, [](int val){
        cout << "模块B收到：" << val*2 << endl;
    });
    // 触发事件
    ed.emit(1001, 666);
    return 0;
}
```

##### 特性：

1.空检查：

```c++
function<void()> f;
if(!f){}//判断是否为空
```

2.可以像普通函数一样调用

```c++
f();
```

3.与函数指针的区别：

| 对比维度                | 函数指针 | std::function  |
| ----------------------- | -------- | -------------- |
| 可装普通全局 / 静态函数 | ✅        | ✅              |
| 可装 Lambda（带捕获）   | ❌        | ✅              |
| 可装仿函数 /std::bind   | ❌        | ✅              |
| 可装类非静态成员函数    | ❌        | ✅              |
| 统一类型存容器          | ❌        | ✅              |
| 保存调用状态            | ❌        | ✅              |
| 安全判空                | ❌ 易崩溃 | ✅ 可判断       |
| 运行开销                | 极低     | 略高（可忽略） |
| C++ 版本                | 原生就有 | C++11 起       |

##### 手写简易`function`

1.抽象基类(提供统一接口)

```c++
template<typename Ret,typename... Args>//...表示一包参数，返回值Ret，这个基类能适配任意返回值+任意参数的函数
struct FuncBase{
virtual ~FuncBase()=default;//虚析构函数，先调子类析构再调基类析构，不加的话delete基类指针只会调用基类析构，子类内存泄漏，编译器自动生成默认实现
virtual Ret invoke(Args&&,,, args)=0;//=0表示这个函数没有实现，强制子类必须实现它
};
```

2.模板派生类

```c++
// 包装具体可调用对象
template<typename Ret, typename... Args, typename F>//F真正的可调用对象
struct FuncImpl : FuncBase<Ret, Args...>
{
    F func;  // 存 lambda/函数/仿函数等可调用对象的地方

    FuncImpl(F f) : func(std::move(f)) {}//std::move避免拷贝

    // 虚函数转发调用
    Ret invoke(Args&&... args) override {//override显式声明是重写虚函数
        return func(std::forward<Args>(args)...);//std::forward完美转发，保持参数的左值右值属性，不拷贝、不修改类型，原汁原味把参数传给内部参数
    }
};

```

3.实现自己的`function`

```c++
template<typename Ret, typename... Args>
class MyFunction
{
private:
    // 持有抽象基类指针，隐藏真实类型
    FuncBase<Ret, Args...>* ptr = nullptr;
public:
    // 接收任意可调用对象
    template<typename F>
    MyFunction(F&& f) {//&&万能指针能接受左值右值lambda函数指针
        // 派生类装真实对象，基类指针指向它
        ptr = new FuncImpl<Ret, Args..., F>(std::forward<F>(f));
    }
    // 重载 () 对外统一调用
    Ret operator()(Args... args) {
        return ptr->invoke(std::forward<Args>(args)...);
    }
    ~MyFunction() { delete ptr; }
};
```

### 三、`std::move`

##### 作用：

单纯做类型强转，把任意一个变量强制转为右值引用&&，不移动数据，只是告诉编译器可以偷资源，真正移动数据的是移动构造函数

```c++
template <typename T>
typename remove_reference<T>::type&& move(T&& t) {
    return static_cast<typename remove_reference<T>::type&&>(t);
}//就是一个强制类型转换
```

##### 右值引用&&

专门用来绑定临时对象实现移动语义

右值引用和普通变量的区别？

`int a=10`的10编译器会在栈上开辟一块独立内存存10,变量a持有这块内存，生命周期由`a`决定，`int&&a=10;`的10是临时右值，不会额外开新内存存10,用完直接销毁

##### 用法

1.移动对象，避免拷贝

```c++
string s1 = "hello world";
string s2 = s1;           // 拷贝，慢
string s3 = move(s1);    // 移动，快！
```

这也是为什么发明右值引用的原因：

老式C++痛点：完整拷贝内存，数据复制一遍，效率低

右值引用：把`s1`的内存资源直接转移给`s3`，`s1`变空，另拷贝极速完成

编译器看到右值优先调用移动构造函数，移动构造函数内部做指针交换

### 四、`std::forward`

##### 作用：

完美转发，把参数的属性(左值右值)完封不动转发给下一个函数

##### 为什么需要`std::forward`

```c++
template<typename T>
void func(T&& t) {
    other_func(t);  // 这里 t 永远变成了 左值！
}
```

即使你传入右值，进入函数后，`t` 有名字了 ，变成左值导致右值属性丢失，无法触发移动语义！

### 五、`std::future`

##### 为什么需要`std::futrue`类?

`std::futrue`是用来获取异步线程的返回值和异常的，是主线程和子线程之间的结果传递通道

一个子线程干完活想把结果告诉主线程，怎么传？需要用到`std::futrue`

`std::future`就是异步任务的结果提货单，拿着单子等线程跑完，再取返回值

##### 特性：

1.`.get()`只能调用一次，一个`future`只能获取一次结果，取完失效，`get()`会阻塞当前线程，直到异步任务完成

2.`bool vaild()`判断当前`future`是否还持有结果

3.`void wait()`只等待完成，不获取结果

4.`wait_for(时间段)`超时等待，不卡死线程

5.`share()`转为`shared_future`,允许多个线程同时获取结果，调用多次`.get()`

##### `std::async`:本质模板函数，发起异步任务返回一个`future`，`future`对象.get()，取任务返回值，等于高级版`thread`，自动管理不用`join`

```c++
// async 是函数，调用它
auto ft = std::async(func);

// ft 是 future 类实例，.get() 是它的成员函数
int res = ft.get();
```

##### `std::packaged_task`:是一个模板类，包装可调用对象的包装器，把函数和`future`绑定在一起，包装一函数，执行任务后结果自动放进`future`,可以手动控制什么时候执行任务

核心三步骤：创建`packaged_task`包装你的函数，从它身上取出`future`,调用`task()`执行任务，`future.get()`拿结果

```c++
#include <iostream>
#include <future>
using namespace std;

int add(int a, int b) {
    return a + b;
}

int main() {
    // 1. 创建 packaged_task，包装函数
    packaged_task<int(int, int)> task(add);

    // 2. 取出 future
    future<int> fu = task.get_future();

    // 3. 执行任务（手动调用）
    task(10, 20);

    // 4. 拿结果
    cout << fu.get() << endl;  // 30
}

```

`async`和`packaged_task`最大的区别：`async`是自动执行，`packaged_task`必须手动调动`task()`才可以

##### `std::promise+std::future`:

`std::promise<T>`：生产者，主动存值、发数据`std::future<T>`：消费者，等待取值、拿数据

```c++
#include <iostream>
#include <thread>
#include <future>
using namespace std;

void setData(promise<int> pro)
{
    // 延迟模拟耗时操作
    this_thread::sleep_for(chrono::seconds(1));
    pro.set_value(666); // 存入数据
}

int main()
{
    promise<int> p;
    future<int> f = p.get_future(); // 绑定成对

    thread t(setData, move(p)); // 移动语义传promise

    cout << "等待子线程赋值...\n";
    int res = f.get(); // 阻塞等待，拿到值才继续
    cout << "收到值：" << res << endl;//res=666

    t.join();
    return 0;
}

```

二者成对绑定，跨线程传值 / 传结果

| 组件                   | 角色                      | 使用场景               | 执行方式             |
| ---------------------- | ------------------------- | ---------------------- | -------------------- |
| `promise+future`       | 主动发值 + 等待收值       | 线程间**手动传递数据** | 手动 set_value 发    |
| `packaged_task+future` | 包装函数 + 获取函数返回值 | 线程池封装任务         | 调用任务自动回填结果 |
| `async+future`         | 一键异步执行              | 简单异步任务           | 自动开线程执行       |





