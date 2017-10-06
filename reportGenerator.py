import csv
import json
import timeit

class Campaign:
    def __init__(self, id="", state="", color="", age="", dates=None, spent=0, actions=None, impressions=0):
        self.id = id
        self.state = state
        self.color = color
        self.age = age
        self.dates = dates or []
        self.spent = spent
        self.actions = actions or {}
        self.impressions = impressions

    def __str__(self):
        return "Campaign: %s\n State: %s\n Color: %s\n Age: %s\n Dates: %s\n Spent: %s\n Actions: %s\n Impressions: %s\n" % (self.id,self.state,self.color,self.age,self.dates,self.spent,self.actions,self.impressions)

class ReportGenerator:
    def __init__(self):
        self.processedData = {'campaigns': {}, 'state': {}, 'colors': {}, 'sources': {}, 'video': {}, 'photo': {}}

    def print_campaign(self, campaign_id):
        print(self.processedData['campaigns'][campaign_id])

    #update the state key in the dictionary with new states while processing the csv
    def add_state(self, state, campaign_id):
        if state in self.processedData['state']:
            self.processedData['state'][state].add(campaign_id)
        else:
            self.processedData['state'][state] = {campaign_id}

    #add the passed in campaign id to the color key
    def add_color(self, color, campaign_id):
        if color in self.processedData['colors']:
            self.processedData['colors'][color].add(campaign_id)
        else:
            self.processedData['colors'][color] = {campaign_id}

    #parse the audience string to split it into the 3 separate fields
    #apply them to the passed in campaign object, and update the state and color keys
    def process_audience(self, campaign, audience, impressions):
        # MT_green_33-38
        audience_params = audience.split('_')
        campaign.state = audience_params[0]
        campaign.color = audience_params[1]
        campaign.age = audience_params[2]
        campaign.impressions += impressions

        self.add_state(audience_params[0], campaign.id)
        self.add_color(audience_params[1], campaign.id)

    #parses the actions and cost for each type of ad
    def process_ad_type(self, type, campaign_id, cost, actions):
        if campaign_id not in self.processedData[type]:
            self.processedData[type][campaign_id] = {'cost': cost, 'actions':{}}
        else:
            self.processedData[type][campaign_id]['cost'] += cost

        for action in actions:
            letter = next(iter(action))
            action_type = action['action']
            count = int(action[letter])

            if action_type in self.processedData[type][campaign_id]['actions']:
                self.processedData[type][campaign_id]['actions'][action_type] += count
            else:
                self.processedData[type][campaign_id]['actions'][action_type] = count

    #helper function to add or create a new action in the dictionary
    def add_sum_action(self, letter, action_type, count):
        if action_type in self.processedData['sources'][letter]['actions']:
            self.processedData['sources'][letter]['actions'][action_type] += count
        else:
            self.processedData['sources'][letter]['actions'][action_type] = count

    #adds the sources to the dictionary sorted by the state they are in
    def add_sources(self, state, letter, action_type, count):
        if letter not in self.processedData['sources']:
            self.processedData['sources'][letter] = {'states':{state: {action_type: count}}, 'actions': {action_type: count}}

        elif state in self.processedData['sources'][letter]['states']:
            if action_type in self.processedData['sources'][letter]['states'][state]:
                self.processedData['sources'][letter]['states'][state][action_type] += count
            else:
                self.processedData['sources'][letter]['states'][state][action_type] = count
        elif state not in self.processedData['sources'][letter]['states']:
            self.processedData['sources'][letter]['states'][state] = {action_type: count}

        self.add_sum_action(letter, action_type, count)

    #adds actions to a campaign
    def process_actions(self, campaign, actions):
        #[{"E": 4, "action": "views"}, {"A": 58, "action": "views"}, {"E": 45, "action": "junk"}]
        for act in actions:
            letter = next(iter(act))
            action_type = act['action']
            count = int(act[letter])

            self.add_sources(campaign.state, letter, action_type, count)

            if letter not in campaign.actions:
                campaign.actions[letter] = {act['action']: act[letter]}

            elif action_type in campaign.actions[letter]:
                campaign.actions[letter][action_type] += count

            elif action_type not in campaign.actions[letter]:
                campaign.actions[letter].update({action_type: count})
            else:
                print('ERROR IN ACTIONS')
                break

    #for each row of the first csv file, create a new campaign object for each new campaign
    #and apply the helper functions to sort the data into the processedData dictionary
    def process_campaign_csv1(self, row):
        campaign_id = row['campaign_id']
        if campaign_id not in self.processedData['campaigns']:

            campaign = Campaign(id=row['campaign_id'])
            audience = row['audience']
            impressions = int(row['impressions'])

            self.process_audience(campaign, audience, impressions)
            self.processedData['campaigns'][campaign_id] = campaign

        else:
            self.processedData['campaigns'][campaign_id].impressions += int(row['impressions'])

    #processes the second csv file and applies the data from each row to it respective campagin object
    def process_campaign_csv2(self, row):
        campaign_id = row['campaign_id']
        campaign_type = row['ad_type']
        date = row['date']
        spend = int(row['spend'])
        actions = json.loads(row['actions'])

        self.process_ad_type(campaign_type,campaign_id, spend, actions)

        campaign = self.processedData['campaigns'][campaign_id]
        campaign.dates.append(date)
        campaign.spent += spend

        self.process_actions(campaign, actions)

    #opens both files and processes the rows
    def process_raw_data(self, csv1, csv2):
        with open(csv1, newline='') as csvfile:
            file_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in file_reader:
                self.process_campaign_csv1(row)

        with open(csv2, newline='') as csvfile:
            file_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in file_reader:
                self.process_campaign_csv2(row)

    #1. what was the total spent against people with purple hair?
    def total_cost_per_hair(self, color):
        campaigns = self.processedData['colors'][color]
        cost = 0
        for campaign in campaigns:
            #print(self.processedData['campaigns'])
            cost = cost + self.processedData['campaigns'][campaign].spent
        return cost
    #2. how many campaigns spent on more than 4 days?
    def min_num_days(self, num_days):
        count = 0
        for campaign in self.processedData['campaigns']:
            if len(self.processedData['campaigns'][campaign].dates) > 4:
                count += 1
        return count
    #3. how many times did sources H report on clicks?
    def calc_report_source(self, source, action):
        return self.processedData['sources'][source]['actions'][action]
    #4. which sources reported more "junk" than "noise"?
    def compare_two_actions(self, act1, act2):
        list_of_sources = []
        for source in self.processedData['sources']:
            if all(k in self.processedData['sources'][source]['actions'] for k in (act1, act2)):
                if self.processedData['sources'][source]['actions'][act1] > self.processedData['sources'][source]['actions'][act2]:
                    list_of_sources.append(source)
        return list_of_sources
    #5. what was the total cost per view for all video ads, truncated to two decimal places?
    def sum_cost_per_action(self, type, action):
        action_sum = 0
        spent = 0
        for campaign in self.processedData[type]:
            spent += self.processedData[type][campaign]['cost']
            if action in self.processedData[type][campaign]['actions']:
                action_sum += self.processedData[type][campaign]['actions'][action]
        #truncated to two decimal places instead of rounding as per the instructions
        return float("{0:.2f}".format(spent / action_sum))
    #6. how many source B conversions were there for campaigns targeting NY?
    def calc_actions_per_source_state(self, source, state, action):
        return self.processedData['sources'][source]['states'][state][action]
    #7. what combination of state and hair color had the best CPM?
    def best_combination_state_hair(self):

        def calc_cpm(cost, impressions):
            return cost / (impressions / 1000)

        def keywithmaxval(d):
            v = list(d.values())
            k = list(d.keys())
            return k[v.index(max(v))]

        max_state = ''
        max_color = ''
        max_cpm = 0
        state_color_dict = {}
        for state in self.processedData['state']:
            state_color_dict[state] = {}
            for campaign in self.processedData['state'][state]:
                color = self.processedData['campaigns'][campaign].color
                cost = self.processedData['campaigns'][campaign].spent
                impressions = self.processedData['campaigns'][campaign].impressions
                if color not in state_color_dict[state]:
                    state_color_dict[state][color] = calc_cpm(cost, impressions)
                else:
                    state_color_dict[state][color] += calc_cpm(cost, impressions)
            temp_max_color = keywithmaxval(state_color_dict[state])
            if max_cpm < state_color_dict[state][temp_max_color]:
                max_cpm = state_color_dict[state][temp_max_color]
                max_color = temp_max_color
                max_state = state
        return max_color, max_state

start = timeit.default_timer()
testing = ReportGenerator()
testing.process_raw_data('source1.csv', 'source2.csv')

print('Question 1:', testing.total_cost_per_hair('purple'))
print('Question 2:', testing.min_num_days(4))
print('Question 3:', testing.calc_report_source('H', 'clicks'))
print('Question 4:', testing.compare_two_actions('junk', 'noise'))
print('Question 5:', testing.sum_cost_per_action('video', 'views'))
print('Question 6:', testing.calc_actions_per_source_state('B', 'NY', 'conversions'))
print('Question 7:', testing.best_combination_state_hair())
stop = timeit.default_timer()

print ("Runtime:", stop - start)


