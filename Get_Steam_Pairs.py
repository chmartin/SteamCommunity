import requests
import json
import argparse
import pandas as pd
    
    
def main():
    """Main function for querying the Steamworks API for player game pairs, produces multiple output files.
    
    Parameters:
        -a, --apps_file -- input string with path/name of input appids file
        -p, --pairs_file -- input string with path/name of input appids/steamids pair file
        -d, --directory_output -- output string with the path to directory for output
        -m, --monitor_file -- output string with the path/name of the output file of processed [appid, steamid] pairs
        -k, --key -- string with API key obtained for use with steam API, will be unique to a specific user
        
    Directory Requirements:
        
    Creates output csv files:
        directory_output/[Appid]_Achievements.csv -- 
        directory_output/[Appid]_Achievements_Summary.csv --
        
    """

    #initialize and parse input arguments
    appid_file_name = ''
    pairs_file_name = ''
    monitor_file_name = ''
    outfile_directory_name = ''
    key = ''
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--apps_file", help="input string with path/name of input appids file")
    parser.add_argument("-p", "--pairs_file", help="input string with path/name of input appids/steamids pair file")
    parser.add_argument("-d", "--directory_output", help="output string with the path to directory for output")
    parser.add_argument("-m", "--monitor_file", help="output string with the path/name of the output file of processed [appid, steamid] pairs")
    parser.add_argument("-k", "--key", help="Directs the key to use for Steamworks API.")
    args = parser.parse_args()
    appid_file_name = args.apps_file
    pairs_file_name = args.pairs_file
    monitor_file_name = args.monitor_file
    outfile_directory_name = args.directory_output
    key = args.key
    
    # read Processed pairs so we don't replicate
    processed = list()
    with open(monitor_file_name, "r+", encoding='utf-8') as file:
        for line in file:
            app_steam_id_pairs = list(map(int, (line.rstrip('\n').split(','))))
            processed.append(app_steam_id_pairs)
    
    # read Appid list which is sorted by priority
    appid_rank = list()
    with open(appid_file_name, "r+", encoding='utf-8') as file:
        for line in file:
            appid = int(line.rstrip('\n'))
            appid_rank.append(appid)
            
    # create dictionary of key:appids value:empty (for now)
    appid_dict = {}
    for appid in appid_rank:
        appid_dict.update({appid:[]})
    #print(appid_dict)
    
    # read Pairs to process and fill them into dict
    with open(pairs_file_name, "r+", encoding='utf-8') as file:
        for line in file:
            app_steam_id_pair = list(map(int, (line.rstrip('\n').split(','))))[1:]
            #print(line)
            #print(app_steam_id_pair)
            appid_dict[app_steam_id_pair[0]].append(app_steam_id_pair[1])
    
    #loop over apps which are sorted by priority
    for appid in appid_rank:
        print("Appid: {0}".format(appid))
        #Get App Summary
        app_summary_url = "http://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid="+str(appid)+"&format=json"
        app_summary_json = {}
        response_app_summary = requests.get(app_summary_url)
        
        if response_app_summary:
            app_summary_json = response_app_summary.json()
        else:
            print('An error has occurred for Application info with id: {0}: {1}.'.format(appid, response_app_summary.status_code))
            #print(url_player_info)
            if response_app_summary.status_code == 429: #This code means you have reached your 100,000 per day limit. So stop spamming them
                exit()
            continue #No basic Achievement Summary information, so let's not waste our time.
            
        app_summary_df = pd.DataFrame(app_summary_json.get("achievementpercentages",{}).get("achievements",{}))
        app_summary_df.to_csv(outfile_directory_name+"/"+str(appid)+"_Achievements_Summary.csv",encoding='utf-8')
        
        #open Achievements csv
        itter = 0
        app_df = pd.DataFrame()
        with open(outfile_directory_name+"/"+str(appid)+"_Achievements.csv","w+",encoding='utf-8') as file3:
            try:
                app_df = (pd.read_csv(file3)).drop('Unnamed: 0', axis='columns',errors='ignore')
            except:
                pass
                
        #Get User info for App
        for steamid in appid_dict[appid]:
            #print("ID Pair: {0}, {1}".format(appid,steamid))
            # omit processed pairs
            if [appid,steamid] in processed:
                continue
                
            #Get App, User Pair
            app_user_url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid="+str(appid)+"&key="+str(key)+"&steamid="+str(steamid)
            app_user_json = {}
            response_app_user = requests.get(app_user_url)
                
            if response_app_user:
                app_user_json = response_app_user.json()
            else:
                print('An error has occurred for Application info with id: {0}, {1}: {2}.'.format(appid, steamid, response_app_user.status_code))                    #print(url_player_info)
                if response_app_user.status_code == 429: #This code means you have reached your 100,000 per day limit. So stop spamming them
                    exit()
                #continue
                    
            app_user_df = pd.DataFrame(app_user_json.get("playerstats",{}).get("achievements",{}))
            gameName = app_user_json.get("playerstats",{}).get("gameName", "")
            if not app_user_df.empty:
                app_user_df['gameName'] = str(gameName)
                app_user_df['steamid'] = str(steamid)
                app_df = pd.concat([app_df,app_user_df],sort=False)
            if itter%100 == 0:
                app_df.to_csv(outfile_directory_name+"/"+str(appid)+"_Achievements.csv", encoding='utf-8')
                print("wrote player game pairs.")
            else:
                print('.')
                
            #write this id to the processed file, but only if it wasn't already there
            with open(monitor_file_name,"r+", encoding='utf-8') as outfile:
                for line in outfile:
                    app_steam_id_pair = (line.rstrip('\n').split(','))
                    if [appid,steamid] in app_steam_id_pair:
                        print("You did the same thing twice, why are you dumb?")
                        break
                else: # not found, we are at the eof
                    outfile.write("{0}, {1}\n".format(appid,steamid)) # append missing data
            
            itter += 1
        #done looping over users for this appid
        app_df.to_csv(outfile_directory_name+"/"+str(appid)+"_Achievements.csv", encoding='utf-8')
        print("Done with {0}".format(appid))

if __name__ == "__main__":
   main()