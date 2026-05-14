# 1. 定义变量并初始化统计计数器
letter_count = 0  # 字母个数
digit_count = 0   # 数字个数
other_count = 0   # 其他字符个数

# 输入第一个字符（注意：input()会读取一行，这里用input()[0]取第一个字符）
print("请逐个输入字符，输入*结束：")
ch = input("请输入一个字符：")[0]

# 2. 利用while循环分类统计，循环条件：输入的字符不是*
while ch != '*':
    # 多分支判断字符类型
    if ch.isalpha():
        letter_count += 1
    elif ch.isdigit():
        digit_count += 1
    else:
        other_count += 1
    # 输入下一个字符，继续循环
    ch = input("请输入下一个字符：")[0]

# 3. 循环结束，输出统计结果
print("\n统计结果：")
print(f"字母个数：{letter_count}")
print(f"数字个数：{digit_count}")
print(f"其他字符个数：{other_count}")
