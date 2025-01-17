from collections import defaultdict
from copy import copy
from decimal import Decimal

import Rounding
from Action import *
from Asset import *
from TaxUtils import getPLNValueDayBefore

# Tax FIFO calculator


class TaxCalculator:
    def __init__(self, account):
        self._account = account
        self._actions = account.actions
        self._assets = defaultdict(list)

    def visitBuySell(self, action):
        if type(action.asset) is Currency:
            return

        data = sum([x[0] for x in self._assets[action.asset]], Decimal(0))
        data2 = data + action.count
        if abs(data2) < abs(data):
            self.visitSell(action)
        else:
            self.visitBuy(action)

    def visitBuy(self, action):
        actions = [x for x in action.flat_actions if not x.actions]
        data = [
            copy(action.count),
            action.count,
            [(getPLNValueDayBefore(x.count, x.asset.ticker, x.time.date().isoformat()), x) for x in actions],
        ]
        self._assets[action.asset].append(data)

    def visitSell(self, action):
        data = self._assets[action.asset]

        count = action.count * Decimal(-1)
        while not count.is_zero():
            if not data:
                raise Exception("Missing assets on sell (%s)" % (str(action.asset)))

            selected = count if count <= data[0][0] else data[0][0]
            precent = selected / data[0][1]
            for pln, act in data[0][2]:
                act.addTaxCalculation(action, pln * precent)
            count -= selected
            data[0][0] -= selected
            if data[0][0].is_zero():
                del data[0]

        actions = [x for x in action.flat_actions if not x.actions]
        for pln, act in [
            (getPLNValueDayBefore(x.count, x.asset.ticker, x.time.date().isoformat()), x) for x in actions
        ]:
            act.addTaxCalculation(action, pln)

    def visitInstant(self, action):
        if not action.actions and type(action.asset) is not Currency:
            return
        actions = [x for x in action.flat_actions if not x.actions] if action.actions else [action]
        for pln, act in [
            (getPLNValueDayBefore(x.count, x.asset.ticker, x.time.date().isoformat()), x) for x in actions
        ]:
            act.addTaxCalculation(action, pln)

    def visitDividend(self, action):
        tax = [x for x in action.flat_actions if x.type == EActionType.TAX]
        precent = Decimal(0)
        income = [x for x in action.flat_actions if x.type == EActionType.INCOME][0]
        if tax and income and tax[0].asset != income.asset:
            raise Exception("Diffrent TAX & INCOME currences in dividends")

        incomeValue = getPLNValueDayBefore(income.count, income.asset.ticker, income.time.date().isoformat())
        if not tax:
            income.addTaxCalculation(action, incomeValue * Decimal(0.19))
            return

        if not tax[0].percent:
            return

        tax[0].addTaxCalculation(
            action, getPLNValueDayBefore(tax[0].count, tax[0].asset.ticker, income.time.date().isoformat())
        )
        income.addTaxCalculation(action, incomeValue * Decimal(0.19))

    def calculate(self):
        for action in self._actions:
            if action.type == EActionType.BUY:
                self.visitBuySell(action)
                continue

            if action.type == EActionType.SELL:
                self.visitBuySell(action)
                continue

            if action.type == EActionType.FEE or action.type == EActionType.FOREX:
                self.visitInstant(action)
                continue

            if action.type == EActionType.DIVIDEND:
                self.visitDividend(action)
                continue
