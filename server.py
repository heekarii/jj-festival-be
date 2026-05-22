# server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, model_validator
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

app = FastAPI()

# CORS: Next.js(3000)에서 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://localhost:3000",
                   "https://festival-jrgq6rxju-choheeseoks-projects.vercel.app",
                   "https://jj-festival-fe.vercel.app",
                   "https://festival.heekari.com"
                   ],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Table(BaseModel):
    id: int
    name: str
    entryTime: Optional[str] = None  # ISO 문자열

class WaitingRequest(BaseModel):
    phone: str
    people: int
    partySize: int

    @model_validator(mode="after")
    def validate_waiting_request(self):
        phone = self.phone
        people = self.people
        party_size = self.partySize

        if not phone or not isinstance(phone, str) or not phone.strip():
            raise ValueError("phone은 빈 문자열이 될 수 없습니다")
        if not isinstance(people, int) or people < 1:
            raise ValueError("people은 1 이상의 정수여야 합니다")
        if party_size != people:
            raise ValueError("partySize는 people과 동일해야 합니다")

        self.phone = phone.strip()
        return self

class WaitingPositionRequest(BaseModel):
    phone: str

class WaitingEntry(BaseModel):
    id: int
    phone: str
    partySize: int

class WaitingResponse(BaseModel):
    id: int
    waitingNumber: int
    phone: str
    partySize: int

# 메모리상에만 저장하는 예시 (총 24개 테이블)
tables: List[Table] = [
    Table(id=i, name=f"테이블 {i}") for i in range(1, 15)
]

waiting_list: List[WaitingEntry] = []
next_waiting_id = 1

@app.get("/tables", response_model=List[Table])
def get_tables():
    return tables

@app.post("/tables/{table_id}/enter", response_model=Table)
def enter_table(table_id: int):
    from zoneinfo import ZoneInfo
    for t in tables:
        if t.id == table_id:
            t.entryTime = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
            return t
    raise HTTPException(404, "테이블이 없습니다")

@app.post("/tables/{table_id}/reset", response_model=Table)
def reset_table(table_id: int):
    for t in tables:
        if t.id == table_id:
            t.entryTime = None
            return t
    raise HTTPException(404, "테이블이 없습니다")

@app.post("/waiting")
def create_waiting(request: WaitingRequest):
    global next_waiting_id

    phone = request.phone.strip()
    for entry in waiting_list:
        if entry.phone == phone:
            return {
            "result": False,
            "message" : "이미 예약 등록한 전화번호입니다."
        }

    entry = WaitingEntry(id=next_waiting_id, phone = phone, partySize=request.people)
    waiting_list.append(entry)
    print(f"대기 등록: {entry}")
    next_waiting_id += 1
    return {"result": True}

@app.post("/waiting/position")
def get_waiting_position(request: WaitingPositionRequest):
    phone = request.phone.strip()
    if not phone:
        return {"result": False}

    for index, entry in enumerate(waiting_list):
        if entry.phone == phone:
            queue_number = index + 1
            return {
                "result": True,
                "queueNumber": queue_number,
                "waitingNumber": queue_number,
            }

    return {"result": False}

@app.get("/waiting", response_model=List[WaitingResponse])
def list_waiting():
    print(f"현재 대기 리스트: {waiting_list}")
    return [
        WaitingResponse(
            id=entry.id,
            waitingNumber=index + 1,
            phone=entry.phone,
            partySize=entry.partySize,
        )
        for index, entry in enumerate(waiting_list)
    ]

@app.post("/waiting/{id}/enter")
def enter_from_waiting(id: int):
    for index, entry in enumerate(waiting_list):
        if entry.id == id:
            del waiting_list[index]
            return {"result": True}
    raise HTTPException(404, "대기 번호가 없습니다")

@app.post("/waiting/{id}/delete")
def delete_waiting(id: int):
    for index, entry in enumerate(waiting_list):
        if entry.id == id:
            del waiting_list[index]
            return {"result": True}
    raise HTTPException(404, "대기 번호가 없습니다")