import json
import time
import requests
from argparse import ArgumentParser


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

    print('Cleaning intermediate snapshots.............')
    parser = ArgumentParser()
 
    parser.add_argument('-app_name','--app_name',required=True,help='Application Name')
    parser.add_argument('-console_url', '--console_url', required=True, help='AIP Console URL')
    parser.add_argument('-console_api_key', '--console_api_key', required=True, help='AIP Console API KEY')

    args=parser.parse_args()

    guid = get_application_guid(args.console_url, args.console_api_key, args.app_name)
    snapshots = check_snapshot(args.console_url, args.console_api_key, guid)


    if len(snapshots) > 1:
        for i in range(0,len(snapshots)-1):
            # print(snapshots[i])
            snapshot_guid = snapshots[i]["guid"]
            snapshot_name = snapshots[i]["name"]
            jobUrl = delete_snapshot(args.console_url, args.console_api_key, args.app_name, guid, snapshot_guid, snapshot_name)
            is_deleted = False
            while not is_deleted:
                is_deleted = check_delete_status(jobUrl, args.console_url, args.console_api_key)
                if is_deleted:
                    print(f"Deleted Snapshot -> {snapshot_name}")
                else:
                    print(f"Deleting Snapshot -> {snapshot_name}............")
                time.sleep(10)
    exit(0)            