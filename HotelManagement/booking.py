# IDK WHAT THE IMPORTS ARE
from math import perm
from os import curdir
from sqlite3.dbapi2 import Cursor
from django.http.response import JsonResponse
from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail
import requests
import sqlite3
import datetime

#-----------Connection to the Database----
# Need to add this cuz of an error. Reason unkonwn.
link = sqlite3.connect("db.sqlite3",check_same_thread=False)
def list_factory(cursor, row):
    lst = []
    for idx, col in enumerate(cursor.description):
        lst.append(row[idx])
    return lst
link.row_factory = list_factory
cursor = link.cursor()
# ------------------------------------------
def bookRoom(request):
    # assuming its a post/get request
    # else get me the customer name/email/id somehow
    if request.method == "GET":
        email       = request.session['email']
        start_date_str  = request.session['fromDate']
        end_date_str    = request.session['toDate']

        # String to Datetime
        x,y,z = [int(i) for i in start_date_str.split("-")]
        start_date  = datetime.date(x,y,z)
        x,y,z = [int(i) for i in end_date_str.split("-")]
        end_date    = datetime.date(x,y,z)

        rooms_booked = []
        room_types =  [[request.session['number_deluxe'],"Deluxe"],
                            [request.session['number_luxury'],"Luxury"],
                            [request.session['number_presidential'],"Presidential"]]
        cursor.execute("""
                        SELECT id 
                        FROM HotelManagement_user
                        WHERE email = :mail""", {'mail':email})
        user_id = cursor.fetchall()

        # IF a user exists:
        if user_id != None and user_id != []:
            user_id = user_id[0][0] #Double Nested ID god damn

            for pair in room_types:
                rooms = int(pair[0])        #This was a string bruh
                room_type = pair[1]
                cursor.execute(""" SELECT room_id,end_date FROM HotelManagement_room
                                WHERE room_type = :suite AND
                                is_empty = 1
                                LIMIT :limit;""",{'suite':room_type,'limit':rooms})
                availableRooms = cursor.fetchall()
                final_list = []
                if availableRooms != []:
                    for myRoom,myDate in availableRooms:
                        if myDate == '':
                            myDate = datetime.date(2000,1,1)
                        final_list.append([myRoom,myDate])

                # print("Available Rooms", availableRooms)
                # print(len(availableRooms),type(rooms))
                # print(final_list)

                # If a room of given category is available
                if availableRooms != None \
                    and availableRooms != [] \
                    and len(availableRooms) == rooms:

                    for room,date in final_list:
                        cursor.execute("""
                                        SELECT end_date FROM HotelManagement_schedule
                                        WHERE room_booked = :id ORDER BY end_date DESC LIMIT 1;""",{'id':room})
                        roomExist = cursor.fetchall()
                        print("Room Exist-", roomExist)
                        print(roomExist[0][0])
                        # if roomExist != []:
                            # roomExist[0][0]
                        if roomExist == [] or roomExist[0][0] < end_date_str:   #See if comparision is correct
                            rooms_booked.append([room,room_type])
                        # START BOOKING ROOMS
                            with link:
                                cursor.execute("""
                                                INSERT INTO HotelManagement_schedule 
                                                (customer_id,start_date,end_date,room_booked,room_type)
                                                VALUES        (:id,:s_date,:e_date,:room_no,:r_type);"""
                                                ,{'id':user_id,'s_date':str(start_date),'e_date':str(end_date),
                                                'room_no':room,'r_type':room_type})
        print("XXXXXXXXX",rooms_booked)

# ------------------------------------------------------------
def LiveUpdate():
    today = datetime.date.today()
    #FLUSHING OUT OLD USERS
    with link:
        cursor.execute("""  UPDATE HotelManagement_room
                            SET customer_id = :cust_id,
                            end_date    = :date,
                            start_date  = :date,
                            is_empty    = :bool,
                            room_id     = :id,
                            room_type   = :type
                            WHERE end_date = :today
                            """,{'cust_id':None,'date':None,'bool':True,'id':None,'type':None,'today':str(today)})

    with link:
        cursor.execute(f"""
                        SELECT * 
                        FROM HotelManagement_schedule
                        WHERE start_date = {str(today)};
                        """)

        newEntries = cursor.fetchall()

        for entry in newEntries:
            cursor.execute(f""" 
                        UPDATE HotelManagement_room
                        SET customer_id = {entry[1]}
                        end_date    = {entry[2]},
                        start_date  = {entry[4]},
                        is_empty    = {False},
                        room_id     = {entry[3]},
                        room_type   = {entry[5]};
            """)
#--------------------------------------------------------------------
