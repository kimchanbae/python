print("======================")
print("     나만의 계산기")
print("======================")

num1 = float(input("첫 번째 숫자 입력: "))
operator = input("연산자 입력 (+, -, *, /): ")
num2 = float(input("두 번째 숫자 입력: "))
num3 = input("세번째 입력:")

if operator == "+":
    result = num1 + num2

elif operator == "-":
    result = num1 - num2

elif operator == "*" and num3 != "cancel":
    result = num1 * num2

elif operator == "/":
    if num2 == 0:
        result = "0으로 나눌 수 없습니다."
    else:
        result = num1 / num2

elif operator == "*" or num3 == "cancel":
    result = "예외사항 일어남"

else:
    result = "잘못된 연산자입니다."

print("----------------------")
print("계산 결과:", result)
print("======================")
