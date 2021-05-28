#import orderbook_helpers as hf
import pandas as pd
from datetime import datetime 
import bisect

# function that converts the time series list of orderbook states into a list of dictionaries for a single side.
def convert_array_to_list_dict(history, pos_limit=5):
    temp_dict = {}
    volm_list = []
    price_list = []
    for i in range(len(history)):
        temp_dict.update({"time":history[i][0]})
        for n in range(pos_limit):
            temp_dict.update({str(n+1):history[i][1][n][1]})
        volm_list.append(temp_dict)
        temp_dict = {}
        temp_dict.update({"time":history[i][0]})
        for n in range(pos_limit):
            temp_dict.update({str(n+1):history[i][1][n][0]})
        price_list.append(temp_dict)
        temp_dict = {}
    return volm_list, price_list

# function that converts the time series list of orderbook states into a list of dictionaries for the signed order book
def convert_array_to_list_dict_sob(history, events, pos_limit=5):
    temp_dict = {}
    volm_list = []
    price_list = []
    print(type(history))
    temp_dict.update({"time":history[0][0]})
    last_volm = history[0][1][0][1]
    for x in range(len(history[0][1])):
        if last_volm + history[0][1][x][1] < last_volm:
            last_volm = history[0][1][x][1]
            pass
        else:
            best_ask_pos = x
            best_bid_pos = x-1
            break
    snap_prices = list(zip(*history[0][1]))[0][(best_bid_pos-(pos_limit-1)):(best_ask_pos+pos_limit)]
    snap_volm = list(zip(*history[0][1]))[1][(best_bid_pos-(pos_limit-1)):(best_ask_pos+pos_limit)]
    for n in range( len(snap_prices)):
        dict_key = n - pos_limit 
        if dict_key >= 0:
            dict_key += 1
        temp_dict.update({str(dict_key):snap_volm[n]})    
    for i in range(len(history)-1):
        temp_dict.update({"time":history[i+1][0]})
        mid_price = float(events[i][6])
        snap_prices = list(zip(*history[i+1][1]))[0]
        snap_volm = list(zip(*history[i+1][1]))
        mid_price_pos = bisect.bisect(snap_prices,mid_price)
        best_bid_pos = mid_price_pos +1
        best_ask_pos = mid_price_pos
        sob_list = snap_prices#[(best_bid_pos-pos_limit):(best_ask_pos + pos_limit )]
        for n in range(len(sob_list)):
            dict_key = n-pos_limit
            if dict_key == 0:
                dict_key +=1
            temp_dict.update({str(dict_key):history[i+1][1][n][1]})
        volm_list.append(temp_dict)
        temp_dict = {}
        temp_dict.update({"time":history[i+1][0]})
        for n in range(len(sob_list)):
            dict_key = n-pos_limit-1
            if dict_key >= 0:
                dict_key += 1
            temp_dict.update({str(dict_key):history[i+1][1][n][0]})
        price_list.append(temp_dict)
        temp_dict = {}
    return volm_list, price_list

#converts pd dfs into an excel file 
def pd_pkl_save(title, hist_obj_dict):
    hist_obj_df = pd.DataFrame(hist_obj_dict)
    hist_obj_df = hist_obj_df[1:]
    path = "./"+title+".pkl"
    hist_obj_df.to_pickle(path)

def pd_csv_save(title, hist_obj_dict):
    hist_obj_df = pd.DataFrame(hist_obj_dict)
    hist_obj_df = hist_obj_df[1:]
    path = "./"+title+".pkl"
    hist_obj_df.to_csv(index=False)

def pd_excel_save(title, hist_obj_dict):
    title +=".xlsx"
    hist_obj_df = pd.DataFrame(hist_obj_dict)
    hist_obj_df = hist_obj_df[1:]
    writer = pd.ExcelWriter(title, engine='xlsxwriter')
    hist_obj_df.to_excel(writer, sheet_name='Sheet1')
    writer.save()



def filesaver(hist_obj, position_range, events=True, **kwargs):
    #hf = converstion_functions()
    list_to_convert = []
    out_time = datetime.utcnow()
    print("recorded the time")
    if 'sides' in kwargs.keys():
        if 'bid' in kwargs['sides']:
            print("found bid okay")
            final_bid_list, final_bid_prices = convert_array_to_list_dict(hist_obj.bid_history, position_range)
            titles_bid = ["L2_orderbook_volm_bid"+str(out_time),
                "L2_orderbook_prices_bid"+str(out_time),
                "L2_orderbook_events_bid"+str(out_time)]
            list_to_convert.append([[final_bid_list, titles_bid[0]], [final_bid_prices, titles_bid[1]]])
            if events:
                list_to_convert[-1].append([hist_obj.bid_events, titles_bid[2]])
                print("added events okay")
        if 'ask' in kwargs['sides']:
            final_ask_list, final_ask_prices = convert_array_to_list_dict(hist_obj.ask_history, position_range)
            titles_ask = ["L2_orderbook_volm_ask"+str(out_time),
                "L2_orderbook_prices_ask"+str(out_time),
                "L2_orderbook_events_ask"+str(out_time)]
            list_to_convert.append([[final_ask_list, titles_ask[0]], [final_ask_prices, titles_ask[1]]])
            if events:
                list_to_convert[-1].append([hist_obj.ask_events, titles_ask[2]])
        if 'signed' in kwargs['sides']:
            final_signed_list, final_signed_prices = convert_array_to_list_dict_sob(hist_obj.signed_history, hist_obj.signed_events)
            titles_signed = ["L2_orderbook_volm_signed"+str(out_time),
                "L2_orderbook_prices_signed"+str(out_time),
                "L2_orderbook_events_signed"+str(out_time)]
            list_to_convert.append([[final_signed_list, titles_signed[0]], [final_signed_prices, titles_signed[1]]])
            if events:
                list_to_convert[-1].append([hist_obj.signed_events, titles_signed[2]])

    else:
        print("no sides specified")

    if 'filetype' in kwargs.keys():
        if 'csv' in kwargs['filetype']:
            for i in range(len(list_to_convert)): # 0 for bid, 1 for ask 2 for signed
                for m in range(len(list_to_convert[i])): # 0 for volm, 1 for price, 2 for events
                    pd_csv_save(list_to_convert[i][m][1], list_to_convert[i][m][0]) # o for data, 1 for title
        if 'pkl' in kwargs['filetype']:
            for i in range(len(list_to_convert)): # 0 for bid, 1 for ask 2 for signed
                for m in range(len(list_to_convert[i])): # 0 for volm, 1 for price, 2 for events
                    pd_pkl_save(list_to_convert[i][m][1], list_to_convert[i][m][0]) # o for data, 1 for title
        if 'xlsx' in kwargs['filetype']:
            for i in range(len(list_to_convert)): # 0 for bid, 1 for ask 2 for signed
                for m in range(len(list_to_convert[i])): # 0 for volm, 1 for price, 2 for events
                    pd_excel_save(list_to_convert[i][m][1], list_to_convert[i][m][0]) # o for data, 1 for title
    else:
        print("no filetype specified")
def main():
    pass

if __name__ == '__main__':
    main()