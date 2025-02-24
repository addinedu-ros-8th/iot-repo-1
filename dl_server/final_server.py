"""
import socket
import struct
import cv2
import numpy as np
import mysql.connector
import json
from deepface import DeepFace
import os
from datetime import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '7625',
    'database': 'abcl'
}

def load_db_embeddings():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT user_name, face_encoding FROM users")
    rows = cursor.fetchall()
    db_embeddings = []
    for user_name, embedding_blob in rows:
        embedding_list = json.loads(embedding_blob)
        embedding_array = np.array(embedding_list, dtype=np.float32)
        db_embeddings.append((user_name, embedding_array))
    cursor.close()
    conn.close()
    return db_embeddings

def find_best_match(face_embedding, db_data, threshold = 4):
    min_distance = float('inf')
    matched_name = "Unknown"
    for db_name, db_emb in db_data:
        dist = np.linalg.norm(face_embedding - db_emb)
        if dist < min_distance:
            min_distance = dist
            matched_name = db_name
    if min_distance > threshold:
        matched_name = "Unknown"
    return matched_name, min_distance

def get_pill_info(user_id):
    current_time = datetime.now().time().strftime("%H:%M:%S")
    current_day = datetime.now().strftime("%A")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT p.pill_name FROM schedule s JOIN pills p ON s.pill_id = p.pill_id "
        "WHERE s.user_id = %s AND s.time = %s AND s.day = %s",
        (user_id, current_time, current_day)
    )
    pill_names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return ",".join(pill_names) if pill_names else "No pills scheduled"

def receive_data(client_socket):
    try:
        data_size = struct.unpack(">I", client_socket.recv(4))[0]
        data = b""
        while len(data) < data_size:
            packet = client_socket.recv(data_size - len(data))
            if not packet:
                return None
            data += packet
        return data
    except socket.error:
        return None

def main():
    SERVER_IP = "127.0.0.1"
    #SERVER_IP = "192.168.0.38"
    SERVER_PORT = 11112
    model_name = "Facenet"

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(1)
    print(f"서버가 {SERVER_IP}:{SERVER_PORT}에서 대기 중입니다...")

    db_embeddings = load_db_embeddings()
    print(f"DB 임베딩 로드 완료: 총 {len(db_embeddings)}개의 임베딩.")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"클라이언트 {addr} 연결됨")
        while True:
            mode = client_socket.recv(2).decode()  # 앞 2글자만 읽기
            if not mode:
                break
            print(f"모드: {mode}")

            if mode == "RG":
                embeddings = []
                received_count = 0
                while received_count < 1:  # 한 장만 처리
                    data = receive_data(client_socket)
                    if data is None:
                        break
                    nparr = np.frombuffer(data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    face_info = DeepFace.represent(img_path=rgb_img, model_name=model_name, enforce_detection=False)
                    if face_info:
                        embeddings.append(np.array(face_info[0]['embedding'], dtype=np.float32))
                        received_count += 1
                        print(f"{received_count}/1 이미지 수신 및 임베딩 완료")
                user_info_data = receive_data(client_socket)
                if user_info_data:
                    user_info = user_info_data.decode().split(",")
                    print("수신된 사용자 정보:", user_info)
                    if embeddings:
                        embedding = embeddings[0].tolist()
                        conn = mysql.connector.connect(**db_config)
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO users (sex, phone, user_name, address, face_encoding) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            tuple(user_info) + (json.dumps(embedding),)
                        )
                        conn.commit()
                        cursor.close()
                        conn.close()
                        db_embeddings.append((user_info[2], np.array(embedding, dtype=np.float32)))
                        print("DB에 저장 완료")

            elif mode == "RC":
                data = receive_data(client_socket)
                if data:
                    nparr = np.frombuffer(data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    embeddings_list = DeepFace.represent(img_path=rgb_img, model_name=model_name, enforce_detection=False)
                    if embeddings_list:
                        current_embedding = np.array(embeddings_list[0]['embedding'], dtype=np.float32)
                        recognized_name, distance = find_best_match(current_embedding, db_embeddings)
                        result = f"{recognized_name},{distance:.2f}"
                    else:
                        result = "Unknown,0.0"
                    client_socket.sendall(struct.pack(">I", len(result.encode())))
                    client_socket.sendall(result.encode())

            elif mode == "PI":
                data = receive_data(client_socket)
                if data:
                    nparr = np.frombuffer(data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    embeddings_list = DeepFace.represent(img_path=rgb_img, model_name=model_name, enforce_detection=False)
                    if embeddings_list:
                        current_embedding = np.array(embeddings_list[0]['embedding'], dtype=np.float32)
                        recognized_name, distance = find_best_match(current_embedding, db_embeddings)
                        if recognized_name != "Unknown":
                            conn = mysql.connector.connect(**db_config)
                            cursor = conn.cursor()
                            cursor.execute("SELECT user_id FROM users WHERE user_name = %s", (recognized_name,))
                            user_id = cursor.fetchone()[0]
                            result = get_pill_info(user_id)
                            cursor.close()
                            conn.close()
                        else:
                            result = "Unknown"
                    else:
                        result = "No Face Detected"
                    client_socket.sendall(struct.pack(">I", len(result.encode())))
                    client_socket.sendall(result.encode())

        client_socket.close()

    server_socket.close()

if __name__ == "__main__":
    main()
"""

import socket
import struct
import cv2
import numpy as np
import mysql.connector
import json
from deepface import DeepFace
import os
from datetime import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

"""
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '7625',
    'database': 'abcl'
}
"""

db_config = {
    'host': '192.168.219.180',
    'user': 'mu',
    'password': '7625',
    'database': 'abcl'
}

def load_db_embeddings():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT user_name, face_encoding FROM users")
    rows = cursor.fetchall()
    db_embeddings = []
    for user_name, embedding_blob in rows:
        if embedding_blob:  # NULL 체크
            embedding_list = json.loads(embedding_blob)
            embedding_array = np.array(embedding_list, dtype=np.float32)
            db_embeddings.append((user_name, embedding_array))
    cursor.close()
    conn.close()
    return db_embeddings

def find_best_match(face_embedding, db_data, threshold=4):
    min_distance = float('inf')
    matched_name = "Unknown"
    for db_name, db_emb in db_data:
        dist = np.linalg.norm(face_embedding - db_emb)
        if dist < min_distance:
            min_distance = dist
            matched_name = db_name
    if min_distance > threshold:
        matched_name = "Unknown"
    return matched_name, min_distance

def get_pill_info(user_id):
    current_time = datetime.now().strftime("%H:%M:%S")  # TIME 형식
    current_day = datetime.now().strftime("%A")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT p.pill_name FROM schedule s JOIN pills p ON s.pill_id = p.pill_id "
        "WHERE s.user_id = %s AND s.time = %s AND s.day_of_the_week = %s",
        (user_id, current_time, current_day)
    )
    pill_names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return ",".join(pill_names) if pill_names else "No pills scheduled"

def receive_data(client_socket):
    try:
        data_size = struct.unpack(">I", client_socket.recv(4))[0]
        data = b""
        while len(data) < data_size:
            packet = client_socket.recv(data_size - len(data))
            if not packet:
                return None
            data += packet
        return data
    except socket.error:
        return None

def main():
    #SERVER_IP = "127.0.0.1"
    SERVER_IP = "192.168.219.124"
    SERVER_PORT = 11113
    model_name = "Facenet"

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(1)
    print(f"서버가 {SERVER_IP}:{SERVER_PORT}에서 대기 중입니다...")

    db_embeddings = load_db_embeddings()
    print(f"DB 임베딩 로드 완료: 총 {len(db_embeddings)}개의 임베딩.")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"클라이언트 {addr} 연결됨")
        while True:
            mode = client_socket.recv(2).decode()
            if not mode:
                break
            print(f"모드: {mode}")

            if mode == "RG":
                embeddings = []
                received_count = 0
                while received_count < 1:
                    data = receive_data(client_socket)
                    if data is None:
                        break
                    nparr = np.frombuffer(data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    face_info = DeepFace.represent(img_path=rgb_img, model_name=model_name, enforce_detection=False)
                    if face_info:
                        embeddings.append(np.array(face_info[0]['embedding'], dtype=np.float32))
                        received_count += 1
                        print(f"{received_count}/1 이미지 수신 및 임베딩 완료")
                user_info_data = receive_data(client_socket)
                if user_info_data:
                    user_info = user_info_data.decode().split(",")
                    print("수신된 사용자 정보:", user_info)
                    if embeddings:
                        embedding = embeddings[0].tolist()
                        conn = mysql.connector.connect(**db_config)
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO users (sex, phone, user_name, address, face_encoding) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            tuple(user_info) + (json.dumps(embedding),)
                        )
                        conn.commit()
                        cursor.close()
                        conn.close()
                        db_embeddings.append((user_info[2], np.array(embedding, dtype=np.float32)))
                        print("DB에 저장 완료")

            elif mode == "RC":
                data = receive_data(client_socket)
                if data:
                    nparr = np.frombuffer(data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    embeddings_list = DeepFace.represent(img_path=rgb_img, model_name=model_name, enforce_detection=False)
                    if embeddings_list:
                        current_embedding = np.array(embeddings_list[0]['embedding'], dtype=np.float32)
                        recognized_name, distance = find_best_match(current_embedding, db_embeddings)
                        result = f"{recognized_name},{distance:.2f}"
                    else:
                        result = "Unknown,0.0"
                    client_socket.sendall(struct.pack(">I", len(result.encode())))
                    client_socket.sendall(result.encode())

            elif mode == "PI":
                data = receive_data(client_socket)
                if data:
                    nparr = np.frombuffer(data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    embeddings_list = DeepFace.represent(img_path=rgb_img, model_name=model_name, enforce_detection=False)
                    if embeddings_list:
                        current_embedding = np.array(embeddings_list[0]['embedding'], dtype=np.float32)
                        recognized_name, distance = find_best_match(current_embedding, db_embeddings)
                        if recognized_name != "Unknown":
                            conn = mysql.connector.connect(**db_config)
                            cursor = conn.cursor()
                            cursor.execute("SELECT user_id FROM users WHERE user_name = %s", (recognized_name,))
                            user_id = cursor.fetchone()[0]
                            result = get_pill_info(user_id)
                            cursor.close()
                            conn.close()
                        else:
                            result = "Unknown"
                    else:
                        result = "No Face Detected"
                    client_socket.sendall(struct.pack(">I", len(result.encode())))
                    client_socket.sendall(result.encode())

        client_socket.close()

    server_socket.close()

if __name__ == "__main__":
    main()
