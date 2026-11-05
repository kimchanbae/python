import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

# ==================================
# 1. 데이터베이스 설정
# ==================================
DB_NAME = "household.db"

def connect_db():
    return sqlite3.connect(DB_NAME)

def create_table():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trans_date TEXT NOT NULL,
                        trans_type TEXT NOT NULL,
                        category TEXT NOT NULL,
                        amount INTEGER NOT NULL,
                        memo TEXT
                        )
                    """)

# ==================================
# 2. 메인 윈도우 설정
# ==================================
root = tk.Tk()
root.title("가계부 관리")
root.geometry("1000x720")
root.minsize(850, 600)
root.configure(bg="#F3F5F8")

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    rowheight=30,
    font=("맑은고딕", 10)
)

style.configure(
    "Treeview.Heading",
    font=("맑은고딕", 10, "bold")
)

# ==================================
# 3. 제목
# ==================================
title = tk.Label(
    root,
    text="나의 가계부",
    font=("맑은 고딕", 22, "bold"),
    bg="#F3F5F8",
    fg="#263445"
)
title.pack(pady=15)

# ==================================
# 4. 요약 화면
# ==================================
summary_frame = tk.Frame(root, bg="#F3F5F8")
summary_frame.pack(fill="x", padx=20, pady=5)

def make_summary(parent, title, color):
    frame = tk.Frame(parent, bg="white", padx=15, pady=12)
    frame.pack(side="left", expand=True, fill="x", padx=5)

    tk.Label(
        frame,
        text=title,
        font=("맑은 고딕", 11),
        bg="white",
        fg="#555555"
    ).pack()

    label = tk.Label(
        frame,
        text="0원",
        font=("맑은 고딕", 18, "bold"),
        bg="white",
        fg=color
    )
    label.pack(pady=5)

    return label

income_label = make_summary(
    summary_frame, "총 수입", "#16834A"
)

expense_label = make_summary(
    summary_frame, "총 지출", "#D94343"
)

balance_label = make_summary(
    summary_frame, "잔액", "#2468B5"
)

# ==================================
# 5. 입력 화면
# ==================================
input_frame = tk.LabelFrame(
    root,
    text=" 거래 등록 ",
    font=("맑은 고딕", 11, "bold"),
    bg="white",
    padx=15,
    pady=12
)
input_frame.pack(fill="x", padx=25, pady=12)

# 날짜
tk.Label(
    input_frame,
    text="날짜",
    bg="white"
).grid(row=0, column=0, padx=5, pady=8)

date_entry = tk.Entry(input_frame, width=15)
date_entry.grid(row=0, column=1, padx=5)
date_entry.insert(0, date.today().isoformat())

# 구분
tk.Label(
    input_frame,
    text="구분",
    bg="white"
).grid(row=0, column=2, padx=5)

type_combo = ttk.Combobox(
    input_frame,
    values=["수입", "지출"],
    width=10,
    state="readonly"
)
type_combo.grid(row=0, column=3, padx=5)
type_combo.set("지출")

# 항목
tk.Label(
    input_frame,
    text="항목",
    bg="white"
).grid(row=0, column=4, padx=5)

category_entry = tk.Entry(input_frame, width=15)
category_entry.grid(row=0, column=5, padx=5)

# 금액
tk.Label(
    input_frame,
    text="금액",
    bg="white"
).grid(row=1, column=0, padx=5, pady=8)

amount_entry = tk.Entry(input_frame, width=15)
amount_entry.grid(row=1, column=1, padx=5)

# 메모
tk.Label(
    input_frame,
    text="메모",
    bg="white"
).grid(row=1, column=2, padx=5)

memo_entry = tk.Entry(input_frame, width=35)
memo_entry.grid(
    row=1, column=3, columnspan=3,
    padx=5, sticky="w"
)

# ==================================
# 6. 월별 조회
# ==================================
filter_frame = tk.Frame(root, bg="#F3F5F8")
filter_frame.pack(fill="x", padx=25, pady=5)

tk.Label(
    filter_frame,
    text="조회 날짜:",
    bg="#F3F5F8",
    font=("맑은 고딕", 10)
).pack(side="left")

month_combo = ttk.Combobox(
    filter_frame,
    width=15,
    state="readonly"
)
month_combo.pack(side="left", padx=8)
# 실행 즉시 오늘 날짜 표시
#month_combo.set(date.today().strftime("%Y-%m-%d"))

# ==================================
# 7. 거래 내역 목록
# ==================================
list_frame = tk.LabelFrame(
    root,
    text=" 거래 내역 ",
    font=("맑은 고딕", 11, "bold"),
    bg="white",
    padx=10,
    pady=10
)
list_frame.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=10
)

columns = (
    "id", "date", "type",
    "category", "amount", "memo"
)

tree = ttk.Treeview(
    list_frame,
    columns=columns,
    show="headings"
)

tree.heading("id", text="번호")
tree.heading("date", text="날짜")
tree.heading("type", text="구분")
tree.heading("category", text="항목")
tree.heading("amount", text="금액")
tree.heading("memo", text="메모")

tree.column("id", width=50, anchor="center")
tree.column("date", width=120, anchor="center")
tree.column("type", width=80, anchor="center")
tree.column("category", width=130, anchor="center")
tree.column("amount", width=140, anchor="e")
tree.column("memo", width=250, anchor="w")

scrollbar = ttk.Scrollbar(
    list_frame,
    orient="vertical",
    command=tree.yview
)

tree.configure(yscrollcommand=scrollbar.set)

tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# ==================================
# 8. 거래 목록 불러오기
# ==================================
def load_data():

    for item in tree.get_children():
        tree.delete(item)

    selected_month = month_combo.get()

    query = """
        SELECT id, trans_date, trans_type,
               category, amount, memo
        FROM transactions
    """

    params = ()

    if selected_month and selected_month != "전체":
        query += " WHERE substr(trans_date, 1, 7) = ?"
        params = (selected_month,)

    query += " ORDER BY trans_date DESC, id DESC"

    with connect_db() as conn:
        rows = conn.execute(query, params).fetchall()

        for row in rows:
            tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    f"{row[4]:,}원",
                    row[5] or ""
                )
            )

        if selected_month and selected_month != "전체":
            where = "WHERE substr(trans_date, 1, 7) = ?"
            total_params = (selected_month,)
        else:
            where = ""
            total_params = ()

        income = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0) "
            f"FROM transactions {where} "
            f"{'AND' if where else 'WHERE'} trans_type = '수입'",
            total_params
        ).fetchone()[0]

        expense = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0) "
            f"FROM transactions {where} "
            f"{'AND' if where else 'WHERE'} trans_type = '지출'",
            total_params
        ).fetchone()[0]

    balance = income - expense

    income_label.config(text=f"{income:,}원")
    expense_label.config(text=f"{expense:,}원")
    balance_label.config(text=f"{balance:,}원")

    update_months()


def update_months():

    with connect_db() as conn:
        months = conn.execute("""
            SELECT DISTINCT substr(trans_date, 1, 7)
            FROM transactions
            ORDER BY 1 DESC
        """).fetchall()

    values = ["전체"] + [m[0] for m in months]

    current = month_combo.get()
    month_combo["values"] = values

    if current in values:
        month_combo.set(current)
    else:
        month_combo.set("전체")

# ==================================
# 9. 거래 등록
# ==================================
def add_transaction():

    trans_date = date_entry.get().strip()
    trans_type = type_combo.get()
    category = category_entry.get().strip()
    amount_text = amount_entry.get().strip()
    memo = memo_entry.get().strip()

    try:
        date.fromisoformat(trans_date)
    except ValueError:
        messagebox.showwarning(
            "입력 오류",
            "날짜를 YYYY-MM-DD 형식으로 입력하세요."
        )
        return

    if not category or not amount_text:
        messagebox.showwarning(
            "입력 오류",
            "항목과 금액을 입력하세요."
        )
        return

    try:
        amount = int(amount_text.replace(",", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showwarning(
            "입력 오류",
            "금액은 0보다 큰 정수로 입력하세요."
        )
        return

    with connect_db() as conn:
        conn.execute("""
            INSERT INTO transactions
            (trans_date, trans_type, category, amount, memo)
            VALUES (?, ?, ?, ?, ?)
        """, (
            trans_date,
            trans_type,
            category,
            amount,
            memo
        ))

    clear_input()
    load_data()

    messagebox.showinfo(
        "등록 완료",
        "거래 내역이 저장되었습니다."
    )

# ==================================
# 10. 입력창 초기화
# ==================================
def clear_input():

    date_entry.delete(0, tk.END)
    date_entry.insert(0, date.today().isoformat())

    type_combo.set("지출")

    category_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    memo_entry.delete(0, tk.END)

    tree.selection_remove(tree.selection())


# ==================================
# 11. 선택 거래 불러오기
# ==================================
def select_transaction(event=None):

    selected = tree.selection()

    if not selected:
        return

    values = tree.item(selected[0], "values")

    date_entry.delete(0, tk.END)
    date_entry.insert(0, values[1])

    type_combo.set(values[2])

    category_entry.delete(0, tk.END)
    category_entry.insert(0, values[3])

    amount_entry.delete(0, tk.END)
    amount_entry.insert(
        0,
        str(values[4]).replace(",", "").replace("원", "")
    )

    memo_entry.delete(0, tk.END)
    memo_entry.insert(0, values[5])


tree.bind("<<TreeviewSelect>>", select_transaction)


# ==================================
# 12. 거래 수정
# ==================================
def update_transaction():

    selected = tree.selection()

    if not selected:
        messagebox.showwarning(
            "선택 오류",
            "수정할 거래를 선택하세요."
        )
        return

    try:
        trans_id = tree.item(selected[0], "values")[0]
        trans_date = date_entry.get().strip()
        date.fromisoformat(trans_date)

        category = category_entry.get().strip()
        trans_type = type_combo.get()
        amount = int(amount_entry.get().strip().replace(",", ""))
        memo = memo_entry.get().strip()

        if not category or amount <= 0:
            raise ValueError

    except ValueError:
        messagebox.showwarning(
            "입력 오류",
            "날짜, 항목, 금액을 올바르게 입력하세요."
        )
        return

    with connect_db() as conn:
        conn.execute("""
            UPDATE transactions
            SET trans_date = ?,
                trans_type = ?,
                category = ?,
                amount = ?,
                memo = ?
            WHERE id = ?
        """, (
            trans_date,
            trans_type,
            category,
            amount,
            memo,
            trans_id
        ))

    load_data()
    clear_input()

    messagebox.showinfo(
        "수정 완료",
        "거래 내역이 수정되었습니다."
    )


# ==================================
# 13. 거래 삭제
# ==================================
def delete_transaction():

    selected = tree.selection()

    if not selected:
        messagebox.showwarning(
            "선택 오류",
            "삭제할 거래를 선택하세요."
        )
        return

    answer = messagebox.askyesno(
        "삭제 확인",
        "선택한 거래를 삭제하시겠습니까?"
    )

    if not answer:
        return

    trans_id = tree.item(selected[0], "values")[0]

    with connect_db() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (trans_id,)
        )

    clear_input()
    load_data()

    messagebox.showinfo(
        "삭제 완료",
        "거래 내역이 삭제되었습니다."
    )


# ==================================
# 14. 버튼 화면
# ==================================
button_frame = tk.Frame(root, bg="#F3F5F8")
button_frame.pack(pady=12)

def make_button(text, command, color):
    return tk.Button(
        button_frame,
        text=text,
        command=command,
        font=("맑은 고딕", 10, "bold"),
        bg=color,
        fg="white",
        activeforeground="white",
        relief="flat",
        padx=18,
        pady=9,
        cursor="hand2"
    )

make_button(
    "거래 등록",
    add_transaction,
    "#218A5B"
).pack(side="left", padx=5)

make_button(
    "수정",
    update_transaction,
    "#3478C8"
).pack(side="left", padx=5)

make_button(
    "삭제",
    delete_transaction,
    "#D34D4D"
).pack(side="left", padx=5)

make_button(
    "새로고침",
    load_data,
    "#64748B"
).pack(side="left", padx=5)

make_button(
    "입력 초기화",
    clear_input,
    "#777777"
).pack(side="left", padx=5)

# 월별 조회 이벤트
month_combo.bind(
    "<<ComboboxSelected>>",
    lambda event: load_data()
)    

# ==================================
# 15. 프로그램 실행
# ==================================
create_table()
load_data()

root.mainloop()