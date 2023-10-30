import json
import time
from cast_common.aipRestCall import AipRestCall
from cast_common.logger import Logger,INFO
import requests
from cast_common.util import format_table
from pandas import ExcelWriter, merge, DataFrame
from argparse import ArgumentParser
from os.path import abspath
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
import psycopg2

def get_application_guid(console_url, console_api_key, app_name):
    url=f"{console_url}/api/applications"
    headers = {
        "x-api-key": console_api_key
    }

    try:
        #fetching the Application list and details.
        rsp = requests.get(url, headers=headers)
        # print(rsp.status_code)
        if rsp.status_code == 200:
            apps = json.loads(rsp.text) 
            for app in apps['applications']:
                if app["name"] == app_name:
                    return app["guid"] 
            print(f'{app_name} application not present in AIP Console')

        else:
            print("Some error has occured! ")
            print(rsp.text)

    except Exception as e:
        print('some exception has occured! \n Please resolve them or contact developers')
        print(e)

def check_snapshot(console_url, console_api_key, guid):
    url=f"{console_url}/api/applications/{guid}/snapshots"
    headers = {
        "x-api-key": console_api_key
    }

    try:
        #fetching the app snapshots.
        rsp = requests.get(url, headers=headers)
        # print(rsp.status_code)
        if rsp.status_code == 200:
            snapshots = json.loads(rsp.text) 

            if len(snapshots)  <= 0:
                print(f'No snapshots found for the Application -> {args.app_name}.\n')
                # add_new_version_and_take_snapshot(args)
                exit(-1)
            else:
                print(f"Snapshots found for the Application -> {args.app_name}.\n")
                return snapshots

        else:
            print("Some error has occured! ")
            print(rsp.text)

    except Exception as e:
        print('some exception has occured! \n Please resolve them or contact developers')
        print(e)

def get_central_schema(console_url, console_api_key, guid):
    url=f"{console_url}/api/aic/applications/{guid}"
    headers = {
        "x-api-key": console_api_key
    }

    try:
        #fetching the app schemas.
        rsp = requests.get(url, headers=headers)
        # print(rsp.status_code)
        if rsp.status_code == 200:
            data = json.loads(rsp.text) 

            if data["schemas"][0]["type"] == 'central':
                return data["schemas"][0]["name"]

        else:
            print("Some error has occured! ")
            print(rsp.text)

    except Exception as e:
        print('some exception has occured! \n Please resolve them or contact developers')
        print(e)

def delete_snapshot(console_url, console_api_key, app_name, guid, snapshot_guid, snapshot_name):
    url = f"{console_url}/api/jobs"
    headers = {
        "x-api-key": console_api_key
    }
    data = {
        "jobType": "delete_snapshot",
        "jobParameters": {
            "appGuid": f"{guid}",
            "appName": f"{app_name}",
            "snapshotGuid": f"{snapshot_guid}",
            "snapshotName": f"{snapshot_name}"
        }
    }

    try:
        #fetching the app snapshots.
        rsp = requests.post(url, headers=headers, json=data)
        # print(rsp.status_code)
        if rsp.status_code == 201:
            res = json.loads(rsp.text) 
            return res["jobUrl"]
        else:
            print("Some error has occured, While deleting a snapshot -> {snapshot_name}")
            print(rsp.text)

    except Exception as e:
        print('some exception has occured! \n Please resolve them or contact developers')
        print(e)

def check_delete_status(jobUrl, console_url, console_api_key):
    url=f"{console_url}{jobUrl}"
    headers = {
        "x-api-key": console_api_key
    }

    try:
        rsp = requests.get(url, headers=headers)
        # print(rsp.status_code)
        if rsp.status_code == 200:
            res = json.loads(rsp.text) 
            if res["state"] == "completed":
                return True
            else:
                return False

        else:
            print("Some error has occured! ")
            print(rsp.text)

    except Exception as e:
        print('some exception has occured! \n Please resolve them or contact developers')
        print(e)


if __name__ == "__main__":

    measures = {
        '60017':'TQI',
        '60013':'Robustness',
        '60014':'Efficiency',
        '60016':'Security',
        '60011':'Transferability',
        '60012':'Changeability'
    }

    parser = ArgumentParser()
    # parser.add_argument('-dashborad_rest_url','--dashborad_rest_url',required=True,help='CAST REST API URL')
    # parser.add_argument('-dashborad_username','--dashborad_username',required=True,help='CAST REST API User Name')
    # parser.add_argument('-dashborad_password','--dashborad_password',required=True,help='CAST REST API Password')
    parser.add_argument('-app_name','--app_name',required=True,help='Application Name')
    parser.add_argument('-console_url', '--console_url', required=True, help='AIP Console URL')
    parser.add_argument('-console_api_key', '--console_api_key', required=True, help='AIP Console API KEY')
    parser.add_argument('-o', '--output', required=False, help='Output Folder')
    parser.add_argument('-css_host','--css_host',required=True,help='CSS Host')
    parser.add_argument('-css_database','--css_database',required=True,help='CSS Database')
    parser.add_argument('-css_port','--css_port',required=True,help='CSS Port')
    parser.add_argument('-css_user','--css_user',required=True,help='CSS User')
    parser.add_argument('-css_password','--css_password',required=True,help='CSS Pasword')

    args=parser.parse_args()
    log = Logger()

    guid = get_application_guid(args.console_url, args.console_api_key, args.app_name)
    snapshots = check_snapshot(args.console_url, args.console_api_key, guid)
    central_schema = get_central_schema(args.console_url, args.console_api_key, guid)

    if len(snapshots) > 2:
        for i in range(1,len(snapshots)-1):
            # print(snapshots[i])
            snapshot_guid = snapshots[i]["guid"]
            snapshot_name = snapshots[i]["name"]
            jobUrl = delete_snapshot(args.console_url, args.console_api_key, args.app_name, guid, snapshot_guid, snapshot_name)
            is_deleted = False
            while not is_deleted:
                is_deleted = check_delete_status(jobUrl, args.console_url, args.console_api_key)
                if is_deleted:
                    print(f"deleted snapshot -> {snapshot_name}.")
                else:
                    print(f"deleting snapshot -> {snapshot_name}............")
                time.sleep(10)

    # aip = AipRestCall(args.dashborad_rest_url, args.dashborad_username, args.dashborad_password, log_level=INFO)
    # if domain_id==None:
    #     log.error(f'Domain not found: {args.app_name}')
    # else:
    #     total = 0
    #     added = 0
    #     snapshot = aip.get_latest_snapshot(domain_id)
    #     if not bool(snapshot):
    #         log.error(f'No snapshots found: {args.app_name}')
    #         exit (-1)
    #     snapshot_id = snapshot['id']

    #     base='./'
    #     if not args.output is None:
    #         base = args.output

    #     s = datetime.now().strftime("%Y%m%d-%H%M%S")
    #     file_name = abspath(f'{base}/violations-{args.app_name}-{s}.xlsx')
    #     writer = ExcelWriter(file_name, engine='xlsxwriter')

    #     first=True
    #     for code in measures:
    #         name = measures[code]
    #         df=aip.get_rules(domain_id,snapshot_id,code,critical=True,non_critical=False,start_row=1,max_rows=999999)
    #         if not df.empty:
    #             if first:
    #                 total=len(df)
                    
    #             df=df.loc[df['diagnosis.status'] == 'added']

    #             if first:
    #                 added=len(df)

    #             detail_df = df[['component.name','component.shortName','rulePattern.name','rulePattern.critical']]
    #             detail_df = detail_df.rename(columns={'component.name':'Component Name','component.shortName':'Component Short Name','rulePattern.name':'Rule','rulePattern.critical':'Critical'})
    #             first=False

    #             if not detail_df.empty:
    #                 format_table(writer,detail_df,name,[120,50,75,10])


    #     log.info(f'{added} new violations added')

    #     # send_email(args.application, args.sender, args.reciever, args.smtp_host, args.smtp_port, args.smtp_user, args.smtp_pass)
    #         # set name of the variable

    db_uri = f"postgresql://{args.css_user}:{args.css_password}@{args.css_host}:{args.css_port}/{args.css_database}"

    # Create an SQLAlchemy engine
    engine  = create_engine(db_uri)

    # Create a connection and a cursor
    connection = engine.connect()
    cursor = connection.connection.cursor()

    # if '.' in args.app_name:
    #     args.app_name = args.app_name.replace('.','_')

    # if '-' in args.app_name:
    #     args.app_name = args.app_name.replace('-','_')

    query = f"""set search_path={central_schema};"""
    cursor.execute(query)

    added_violation_query = """SELECT count(distinct(concat(cvs.diag_id,cvs.object_id)))
    FROM csv_violation_statuses cvs , csv_quality_tree cqt
    WHERE cqt.metric_id = diag_id and m_crit =1
    AND cvs.snaphot_id IN (SELECT max (snapshot_id ) 
    FROM dss_snapshots) AND cvs.violation_status='Added'"""

    # Execute the query
    cursor.execute(added_violation_query)

    # Fetch all the rows (column values) from the result
    added = cursor.fetchall()

    added = added[0][0]

    name = 'added_violations'

    # set value of the variable

    value = added

    # set variable

    print(f'##vso[task.setvariable variable={name};]{value}')

    print(added) 
        
    exit(added)
