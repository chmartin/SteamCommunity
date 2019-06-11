import requests
import json
import argparse
import pandas as pd
    
    
def main():
    """Main function for querying the Steamworks API, produces multiple output files.
    
    Parameters:
        -f, --file -- input string with path/name of input steamids file
        -o, --output -- output string with path for processed steamids output file
        -k, --key -- string with API key obtained for use with steam API, will be unique to a specific user
        
    Directory Requirements:
        These files must already be present in directory (can be obtained from: Root_User.ipynb) and will be updated.
        
        player_info.csv -- Player Profile Information
        player_game_info.csv -- Game Information for users with public facing profile
        player_friend_info.csv -- Friends Information for users with public facing profile
        [output].txt -- a txt file with processed steamids
        
    Creates output text file:
        Steam_User_Next_Friends.txt -- a txt file with all friends of the input steamids, can be used as input if user wants to pass as input next time.
        
    """

    #initialize and parse input arguments
    id_file_name = ''
    id_outfile_name = ''
    key = ''
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="Directs the input steamids file to a name of your choice")
    parser.add_argument("-o", "--output", help="Directs the processed steamids output to a name of your choice")
    parser.add_argument("-k", "--key", help="Directs the key to use for Steamworks API.")
    args = parser.parse_args()
    id_file_name = args.file
    id_outfile_name = args.output
    key = args.key
    
    # read Processed steamids so we don't replicate
    processed = list()
    with open(id_outfile_name, "r+", encoding='utf-8') as file:
        for line in file:
            #print(line)
            processed.append(line.rstrip('\n'))
    
    #let's not go crazy
    if len(processed) > 1000000:
        exit()
    #print(processed)
    
    #initialize variables for loop
    new_ids = list()
    itter = 0
    
    #Open csv's to output
    player_info_orig = (pd.read_csv('player_info.csv', encoding='utf-8')).drop('Unnamed: 0', axis='columns')
    player_game_info_orig = (pd.read_csv('player_game_info.csv', encoding='utf-8')).drop('Unnamed: 0', axis='columns')
    player_friend_info_orig = (pd.read_csv('player_friend_info.csv', encoding='utf-8')).drop('Unnamed: 0', axis='columns')
    
    #Start looping over input steamids
    with open(id_file_name, "r+", encoding='utf-8') as file:
        for steam_id_in in file:
        
            steam_id_in = steam_id_in.rstrip('\n')
            print("ID input: {0}".format(steam_id_in))
            
            #Move on if processed
            if steam_id_in in processed:
                continue
                
            #Query Steamworks API
            url_player_info = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="+(key)+"&steamids="+(steam_id_in)
            url_player_game_info = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key="+(key)+"&steamid="+(steam_id_in)+"&include_played_free_games=true"
            url_player_friend_info = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key="+(key)+"&steamid="+(steam_id_in)+"&relationship=friend"
            print("ID not already processed: {0}".format(steam_id_in))
            player_info_json = {}
            player_game_info_json = {}
            player_friend_info_json = {}
            
            response_player_info = requests.get(url_player_info)
            if response_player_info:
                #print(response_player_info.status_code)
                player_info_json = response_player_info.json()
            else:
                print('An error has occurred for player info with id: {0}: {1}.'.format(steam_id_in, response_player_info.status_code))
                #print(url_player_info)
                if response_player_info.status_code == 429: #This code means you have reached your 100,000 per day limit. So stop spamming them
                    player_info_orig.to_csv('player_info.csv', encoding='utf-8')
                    player_game_info_orig.to_csv('player_game_info.csv', encoding='utf-8')
                    player_friend_info_orig.to_csv('player_friend_info.csv', encoding='utf-8')
                    exit()
                continue #No basic profile information, so let's not waste our time.
                
            response_player_game_info = requests.get(url_player_game_info)
            if response_player_game_info:
                player_game_info_json = response_player_game_info.json()
            else:
                print('An error has occurred for player game info with id: {0}: {1}.'.format(steam_id_in, response_player_game_info.status_code))
                if response_player_game_info.status_code == 429:
                    player_info_orig.to_csv('player_info.csv', encoding='utf-8')
                    player_game_info_orig.to_csv('player_game_info.csv', encoding='utf-8')
                    player_friend_info_orig.to_csv('player_friend_info.csv', encoding='utf-8')
                    exit()
                #continue #No need to continue in this case, maybe this user is useful for other information?
                
            response_player_friend_info = requests.get(url_player_friend_info)
            if response_player_friend_info:
                player_friend_info_json = response_player_friend_info.json()
            else:
                print('An error has occurred for player friend info with id: {0}: {1}.'.format(steam_id_in, response_player_friend_info.status_code))
                #print(url_player_friend_info)
                if response_player_friend_info.status_code == 429:
                    player_info_orig.to_csv('player_info.csv', encoding='utf-8')
                    player_game_info_orig.to_csv('player_game_info.csv', encoding='utf-8')
                    player_friend_info_orig.to_csv('player_friend_info.csv', encoding='utf-8')
                    exit()
                #continue #No need to continue in this case, maybe this user is useful for other information?
    
            #Convert to DF and concat to existing information
            player_info_df = pd.DataFrame(player_info_json.get('response',{}).get('players'))
            player_info_orig = pd.concat([player_info_orig,player_info_df],sort=False)
            #Save every 100 Users
            if itter%100 == 0:
                player_info_orig.to_csv('player_info.csv', encoding='utf-8')
                print("wrote player info.")
            else:
                print('.')
            player_game_info_df = pd.DataFrame(player_game_info_json.get('response',{}).get('games'))
            if not player_game_info_df.empty:
                player_game_info_df['steamid'] = str(steam_id_in)
                player_game_info_orig = pd.concat([player_game_info_orig,player_game_info_df],sort=False)
            if itter%100 == 0:
                player_game_info_orig.to_csv('player_game_info.csv', encoding='utf-8')
                print("wrote player game info.")
            else:
                print('.')
            player_friend_info_df = pd.DataFrame(player_friend_info_json.get('friendslist',{}).get('friends'))
            if not player_friend_info_df.empty:
                player_friend_info_df['steamid_orig'] = str(steam_id_in)
                player_friend_info_orig = pd.concat([player_friend_info_orig,player_friend_info_df],sort=False)
            if itter%100 == 0:
                player_friend_info_orig.to_csv('player_friend_info.csv', encoding='utf-8')
                print("wrote player friend info.")
            else:
                print('.')
            #if we can read the columns of the friends DF lets save those friends so we can use them later
            if 'steamid' in player_friend_info_df.columns.to_list():
                new_ids = list(set(new_ids + (player_friend_info_df['steamid'].to_list()))) #Check they are unique
            
            #write this id to the processed file, but only if it wasn't already there
            with open(id_outfile_name,"r+", encoding='utf-8') as outfile:
                for line in outfile:
                    if steam_id_in in line:
                        print("You did the same thing twice, why are you dumb?")
                        break
                else: # not found, we are at the eof
                    outfile.write(steam_id_in+'\n') # append missing data
    
            #Save next group of friends
            with open("Steam_User_Next_Friends.txt","w+", encoding='utf-8') as file2:
                next_ids = list(set(processed + new_ids))
                for id in next_ids:
                    file2.write("{0}\n".format(id))
            
            itter += 1
    
    #we are done, save
    player_info_orig.to_csv('player_info.csv', encoding='utf-8')
    player_game_info_orig.to_csv('player_game_info.csv', encoding='utf-8')
    player_friend_info_orig.to_csv('player_friend_info.csv', encoding='utf-8')

if __name__ == "__main__":
   main()