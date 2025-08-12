import random
import string

def generate_token(group_num, member_num):
    tokens = []
    for g in range(1, group_num + 1):
        for m in range(1, member_num + 1):
            group_str = str(g).zfill(3)
            member_str = str(m).zfill(3)
            rand_str = ''.join(random.choices(string.ascii_lowercase, k=3))
            token = f"{group_str}_{member_str}_{rand_str}"
            tokens.append(token)
    return tokens

if __name__ == "__main__":
    group_num = int(input("请输入组数: "))
    member_num = int(input("请输入每组成员人数: "))
    tokens = generate_token(group_num, member_num)
    with open("token.txt", "w", encoding="utf-8") as f:
        f.write(f"group_num: {group_num},member_num: {member_num}\n")
        for token in tokens:
            f.write(token + "\n")
    print(f"已生成 {len(tokens)} 个 Token，保存在 token.txt")