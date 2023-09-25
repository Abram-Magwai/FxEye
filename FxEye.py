import argparse
from bs4 import BeautifulSoup
import requests
import sys



days_closes = [1.06920, 1.0900, 1.0695, 1.0698, 1.0700, 1.0670]


def update_line(file_path, line_number_to_update, new_content):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        if 1 <= line_number_to_update <= len(lines):
            lines[line_number_to_update - 1] = new_content

            with open(file_path, 'w') as file:
                file.writelines(lines)
                print(f"alert {line_number_to_update} updated successfully.")
        else:
            print(f"Line number {line_number_to_update} is out of range.")

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def delete_line(file_path, line_number_to_delete):
    try:
        # Read the file into a list
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Check if the line number to delete is valid
        if 1 <= line_number_to_delete <= len(lines):
            # Remove the line by its index (line_number_to_delete - 1)
            del lines[line_number_to_delete - 1]

            # Write the modified list back to the file
            with open(file_path, 'w') as file:
                file.writelines(lines)
                print(f"Line {line_number_to_delete} deleted successfully.")
        else:
            print(f"Line number {line_number_to_delete} is out of range.")

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")



def convert_currency_pair(currency_pair):
    if len(currency_pair) == 6:
        return f"{currency_pair[:3]}-{currency_pair[3:]}"
    else:
        return "Invalid currency pair format"

def get_current_market_price(symbol):
    url_symbol = convert_currency_pair(currency_pair=symbol)
    url =  f"https://za.investing.com/currencies/{url_symbol}"

    sys.stdout.write(f'\rFetching data for {symbol}...')

    response = requests.get(url)
    if response.status_code == 200:

        sys.stdout.write('\rObtained data for...')
        sys.stdout.write('\rExtractring current price...')


        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        price_node = soup.find_all(class_='last-price-value')[1]
        return float(price_node.text.replace(",", ""))
    else:
        print("Failed to retrieve the web page.")


def pair(value: str):
    if len(value) == 6:
        return value
    raise argparse.ArgumentTypeError(f"Pair should only be 6 characters e.g eurusd")



def manage_alerts(pair: str, resistance, support):
    pair_index = find_pair_index(pair)
    if pair_index == -1:
        with open('trade_plans.txt', 'a') as file:
            trade = f'pair: {str(pair).lower()}, '
            if resistance is not None:
                trade += f'resistance: {resistance}, '
            if support is not None:
                trade += f'support: {support}\n'
            file.write(trade)
    else:
        line = None
        line_resistance = None
        line_support = None

        with open('trade_plans.txt', 'r') as file:
            lines = file.readlines()
            line = lines[pair_index-1]
            line_details = line.split(',')

            if len(line_details) == 3:
                line_resistance = line_details[1].split(':')[1].strip()
                line_support = line_details[2].split(':')[1].strip()
            else:
                if 'resistance' in line_details[1]:
                    line_resistance = line_details[1].split(':')[1].strip()
                else:
                    line_support = line_details[1].split(':')[1].strip()

        line = f'pair: {str(pair).lower()}, '
        if line_resistance is not None:
                line += f'resistance: {line_resistance if resistance is None else resistance}, '
        if line_support is not None:
            line += f'support: {line_support if support is None else support}'

        update_line('trade_plans.txt', pair_index, line+'\n')




def find_pair_index(pair: str):
    line_to_delete = -1
    try:
        with open('trade_plans.txt', 'r') as file:
            file_lines = file.readlines()
            for index in range(len(file_lines)):
                line = file_lines[index]
                if pair in line:
                    #delete this line
                    line_to_delete = index+1
                    break
    except IOError:
        return line_to_delete
    return line_to_delete

def check_broken_levels():
    try:
        with open('trade_plans.txt', 'r') as file:
            alerts = file.readlines()
            for alert in alerts:
                alert_details = alert.split(',')
                pair = alert_details[0].split(':')[1].strip()

                current_price = get_current_market_price(pair)
                sys.stdout.write('\rDetermining broken levels...')

                if 'resistance' in alert:
                    alert_resistance = alert_details[1].split(':')[1].strip()
                    if float(alert_resistance) < current_price:
                        print(f'\t{pair} successfully broke resistance @ {alert_resistance}... Look for trading opportunities 😃🎉🎈\\n')
                        #remove resistance from line
                        pair_index = find_pair_index(pair=pair)
                        line = f'pair: {pair}, '
                        if len(alert_details) == 3:
                            alert_support = alert_details[2].split(':')[1].strip()
                            line += f'support: {alert_support}'                        
                            update_line('trade_plans.txt', pair_index, line)
                        else:
                            delete_line('trade_plans.txt', pair_index)
                    
                if 'support' in alert:
                    if len(alert_details) == 3:
                        alert_support = alert_details[2].split(':')[1].strip()
                    else:
                        alert_support = alert_details[1].split(':')[1].strip()

                    if float(alert_support) > current_price:
                        print(f'{pair} successfully broke support @ {alert_support}... Look for trading opportunities 😃🎉🎈\n')

                        pair_index = find_pair_index(pair=pair)
                        line = f'pair: {pair}, '
                        if len(alert_details) == 3:
                            alert_resistance = alert_details[1].split(':')[1].strip()
                            line += f'resistance: {alert_resistance}'                        
                            update_line('trade_plans.txt', pair_index, line)
                        else:
                            delete_line('trade_plans.txt', pair_index)
                            pass
                          
    except IOError:
        print('No trading alerts found, check help document on how to add alerts')
    print('Done... ')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Foreign Exchange market script to set support and resistance for specific currency and check when market has broken the boundaries')
    parser.add_argument('-c', '--check', action='store_true', required='--add' not in sys.argv, help='Check for broken support or resistance levels')
    parser.add_argument('-a', '--add', action='store_true', required='--check' not in sys.argv, help='Set boundaries')
    parser.add_argument('-p', '--pair', type=pair, required='--a' in sys.argv, help='Pair name')


    parser.add_argument('-r', '--resistance', type=float, help='Resistance level rate, e.g 1.0800')
    parser.add_argument('-s', '--support', type=float, help='Support level rate, e.g 1.0800')

    args = parser.parse_args()
    pair = None
    support = None
    resistance = None

    if args.add:
        if not args.pair:
            parser.error("--pair is required when --add is provided.")
        if not (args.support or args.resistance):
            parser.error("--support or --resistance (or both) are required when --add is provided.")
        
        pair = args.pair
        support = None
        resistance = None
        if args.resistance is not None:
            resistance = args.resistance
        if args.support is not None:
            support = args.support

        manage_alerts(pair=pair, resistance=resistance, support=support)
    elif args.check:
        check_broken_levels()
        pass
    