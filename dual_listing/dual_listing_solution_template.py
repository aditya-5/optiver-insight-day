import time

from optibook.synchronous_client import Exchange

# These are the instruments which we are trading. Refer to the assignment description for a more detailed explanation.
LIQUID_INSTRUMENT = 'PHILIPS_A'
ILLIQUID_INSTRUMENT = 'PHILIPS_B'


class TopOfBook:
    """
    The 'TopOfBook' contains the best bid price and volume, as well as the best ask price and volume.

    It is possible that sometimes there is only one side present, meaning we only have an order on the bid side or on
    the ask side. In this case the 'has_bid_and_ask' field is set to false.

    Attributes
    ----------
    best_bid_price: float or None
        The price of the best bid in the order book that this function received as a parameter.
        If there are no bids in the order book, this is set to None.

    best_bid_volume: float or None
        The volume of the best bid in the order book that this function received as a parameter.
        If there are no bids in the order book, this is set to None.

    best_ask_price: float or None
        The price of the best ask in the order book that this function received as a parameter.
        If there are no asks in the order book, this is set to None.

    best_ask_volume: float or None
        The volume of the best ask in the order book that this function received as a parameter.
        If there are no asks in the order book, this is set to None.
    """
    def __init__(self,
                 best_bid_price,
                 best_bid_volume,
                 best_ask_price,
                 best_ask_volume):
        # top the of bid side (i.e. best bid), this can be None if the bid side is empty
        self.best_bid_price = best_bid_price
        self.best_bid_volume = best_bid_volume

        # top the of ask side (i.e. best ask), this can be None if the ask side is empty
        self.best_ask_price = best_ask_price
        self.best_ask_volume = best_ask_volume

    def has_bid_and_ask(self):
        """
        If this returns True, you have a guarantee that all of the above fields have values.

        It returns True if there are bids and asks in the order book, and false if one or the other is empty,
        resulting in two of the values above to be None.
        """
        return self.best_bid_price is not None and self.best_ask_price is not None


class AutoTrader:
    """
    This is the "main" class which houses our algorithm. You will see there are a few helper functions already here,
    as well as a main "trade" function which runs the algorithm. We've done some work for you already there, but you
    will need to write the bulk of the strategy yourself.
    """
    def __init__(self):
        self.exchange_client = Exchange()

    def connect(self):
        """
        Connect to the optibook exchange
        """
        self.exchange_client.connect()

    def get_order_book_for_instrument(self, instrument):
        return self.exchange_client.get_last_price_book(instrument)

    def get_position_for_instrument(self, instrument):
        positions = self.exchange_client.get_positions()
        return positions[instrument]

    def get_top_of_book(self, order_book):
        """
        Get the best bid and best ask of the order book you pass in as a parameter.
        """
        best_bid_price = None
        best_bid_volume = None
        if len(order_book.bids) > 0:
            best_bid_price = round(order_book.bids[0].price, 2)
            best_bid_volume = round(order_book.bids[0].volume, 2)

        best_ask_price = None
        best_ask_volume = None
        if len(order_book.asks) > 0:
            best_ask_price = round(order_book.asks[0].price, 2)
            best_ask_volume = round(order_book.asks[0].volume, 2)

        return TopOfBook(best_bid_price, best_bid_volume, best_ask_price, best_ask_volume)

    def print_top_of_book(self, instrument, top_of_book):
        print(f'[{instrument}] bid({top_of_book.best_bid_volume}@{top_of_book.best_bid_price})-ask({top_of_book.best_ask_volume}@{top_of_book.best_ask_price})')

    def insert_buy_order(self, instrument, price, volume, order_type):
        """
        Insert an order to buy. Note that volume must be positive. Also note that you have no guarantee that your
        order turns into a trade.

        instrument: str
            The name of the instrument to buy.

        price: float
            The price level at which to insert the order into the order book on the bid side.

        volume: int
            The volume to buy.

        order_type: int
            You can set this to 'limit' or 'ioc'. 'limit' orders stay in the book while any remaining volume of an
            'ioc' that is not immediately matched is cancelled.

        return:
            an InsertOrderReply containing a request_id as well as an order_id, the order_id can be
            used to e.g. delete or amend the limit order later.
        """
        return self.exchange_client.insert_order(instrument, price=price, volume=volume, side='bid', order_type=order_type)

    def insert_sell_order(self, instrument, price, volume, order_type):
        """
        Insert an order to sell. Note that volume must be positive. Also note that you have no guarantee that your
        order turns into a trade.

        instrument: str
            The name of the instrument to sell.

        price: float
            The price level at which to insert the order into the order book on the ask side.

        volume: int
            The volume to sell.

        order_type: int
            You can set this to 'limit' or 'ioc'. 'limit' orders stay in the book while any remaining volume of an
            'ioc' that is not immediately matched is cancelled.

        return:
            an InsertOrderReply containing a request_id as well as an order_id, the order_id can be
            used to e.g. delete or amend the limit order later.
        """
        return self.exchange_client.insert_order(instrument, price=price, volume=volume, side='ask', order_type=order_type)

    def trade(self):
        """
        This function is the main trading algorithm. It is called in a loop, and in every iteration of the loop
        we do the exact same thing.

        We start by getting the order books, formatting them a little bit and then you will have to make a trading
        decision based on the prices in the order books.
        """

        # First we get the current order books of both instruments
        full_book_liquid = self.get_order_book_for_instrument(LIQUID_INSTRUMENT)
        full_book_illiquid = self.get_order_book_for_instrument(ILLIQUID_INSTRUMENT)

        # Then we extract the best bid and best ask from those order books
        top_book_liquid = self.get_top_of_book(full_book_liquid)
        top_book_illiquid = self.get_top_of_book(full_book_illiquid)

        # If either the bid side or ask side is missing, in the order books, then we stop right here and wait for the
        # next cycle, in the hopes that then the order books will have both the bid and ask sides present
        if not top_book_liquid.has_bid_and_ask() or not top_book_illiquid.has_bid_and_ask():
            print('There are either no bids or no asks, skipping this trade cycle.')
            return

        # Print the top of each book, this will be very helpful to you when you want to understand what your
        # algorithm is doing. Feel free to add more logging as you see fit.
        self.print_top_of_book(LIQUID_INSTRUMENT, top_book_liquid)
        self.print_top_of_book(ILLIQUID_INSTRUMENT, top_book_illiquid)
        print('')

        # Trade!
        # Take if from here, and implement your actual strategy with the help of the pre-processing we have done for you
        # above. Note that this is very rudimentary, and there are things we have left out (e.g. position management is
        # missing, hedging is missing, and how much credit you ask for is also missing).
        #
        # Maybe a first step is to run this code as is, and see what it prints out to get some inspiration if you are
        # stuck. Otherwise, come to us, we are always happy to help. Check the client documentation for all the
        # functions that are at your disposal.
        #
        # -----------------------------------------
        # TODO: Implement trade logic here
        # -----------------------------------------
        
        


def main():
    auto_trader = AutoTrader()
    auto_trader.connect()

    while True:
        auto_trader.trade()
        time.sleep(0.1)


if __name__ == "__main__":
    main()
