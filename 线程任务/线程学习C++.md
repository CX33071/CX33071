1.每个进程开始默认有一个主线程,运行这个程序时操作系统先创建一个进程，进程创建完成后操作系统会立即在这个进程里创建主线程，这个主线程是进程的默认执行流
2.创建线程对象：
std::thread t(第一个参数是线程要执行的 “任务函数”，后续参数是传递给这个任务函数的参数);
std::this_thread::sleep_for() 接收一个时间间隔作为参数，让当前线程休眠指定的时间长度    std::this_thread::sleep_for(std::chrono::seconds(3));
t.join()：主线程阻塞，直到子线程 t 执行完毕，这是最安全的线程等待方式，避免 “僵尸线程” 或程序崩溃
运行结果会看到主线程和子线程的输出交替出现（并发执行）
3.线程分离
如果主线程不需要等待子线程完成，可以使用 detach() 将线程分离
int main() {
    std::thread t(func);
    t.detach();  // 分离线程，主线程无需等待
    std::cout << "主线程执行完毕，即将退出" << std::endl;
    // 主线程休眠3秒，确保分离线程能执行完（否则主线程退出会终止所有线程）
    std::this_thread::sleep_for(std::chrono::seconds(3));
    return 0;
}
分离后的线程不能再调用 join()，否则会抛出 std::system_error 异常。
主线程退出前，需确保分离线程完成必要操作，否则线程会被强制终止
4.检查线程是否可连接（joinable ()）
joinable() 用于判断线程对象是否关联了一个可执行的线程（未调用 join() 或 detach()）
if(t.joinable()){
    t.join();
}
5.传递参数给线程函数
普通参数示例1
传递引用/指针：std::ref()包装引用，否则会被拷贝
std::thread t(func, std::ref(n));
6.加锁解锁
std::mutex mutex;   全局互斥锁
mutex.lock()加锁
mutex.unlock()解锁
优化：std::lock_guard(RAII机制),自动加锁/解锁，避免忘记解锁导致死锁
构造时加锁，析构时解锁
std::unique_lock是功能最丰富的自动锁，支持手动加锁/解锁、延迟加锁、转移所有权，是std::condition_variable的为一适配锁，wait()要求传入unique_lock
    构造时可选择是否立即加锁（延迟加锁）；
    支持手动调用 lock()/unlock()，灵活控制锁的生命周期；
    可移动（std::move），但不可拷贝；
    析构时若持有锁，则自动解锁
    std::mutex mtx;
    void func() {
    // 1. 延迟加锁：构造时不加锁，后续手动加锁
    std::unique_lock<std::mutex> lock(mtx, std::defer_lock);
    std::cout << "准备加锁..." << std::endl;
    lock.lock();  // 手动加锁
    std::cout << "已加锁，执行临界区代码" << std::endl;
    // 临界区操作...
    lock.unlock();  // 手动解锁（提前释放锁，提高并发）
    
    std::cout << "临时解锁后，执行非临界区代码" << std::endl;
    
    lock.lock();  // 再次加锁
    std::cout << "再次加锁，执行剩余临界区代码" << std::endl;
    // 析构时自动解锁
    }
    int main() {
    std::thread t(func);
    t.join();
    return 0;
    }
7.条件变量
条件变量用于线程间的同步通信，解决 “轮询等待” 的低效问题（比如一个线程等待另一个线程完成某个操作后再执行），常与互斥锁配合使用
std::condition_variable：条件变量对象，提供 wait()、notify_one()、notify_all() 三个核心方法。
    wait(lock)：阻塞当前线程，释放锁，直到被其他线程通知唤醒，唤醒后重新获取锁。
    notify_one()：唤醒等待该条件变量的一个线程。
    notify_all()：唤醒等待该条件变量的所有线程。
必须与 std::unique_lock<std::mutex> 配合（而非 lock_guard），因为 wait() 需要临时释放锁
cv.wait(lock, 条件)：第二个参数是 “唤醒条件”，避免 “虚假唤醒”（系统层面的无意义唤醒），只有条件为 true 时才会真正唤醒线程
8.原子操作
std::atomic<T>：原子类型模板，支持 ++、--、+=、= 等操作，所有操作都是原子的，不会出现数据竞争
    std::atomic<int> count(0);
    若想对int a原子操作就是定义一个原子整型a
9.获取CPU核心数
unsigned int cores=std::thread::hardware_concurrency();