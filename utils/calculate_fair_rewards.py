def calculate_rewards():
    """
    This interactive script can be used to estimate fair rewards per assignment for crowdsourcing tasks.

    The user is asked to input an estimated time it takes for a worker to complete one task suite. 
    The function then outputs a reward that results in an average hourly wage of $12.

    How to use: run this python file in the terminal and follow instructions
    """

    print("\nCalculate a fair reward per task suite by inputting the estimated time spent for one task suite. \n"
          "The calculator calculates a reward that results in an hourly pay of $12. \n")

    while True:

        time_per_suite = input("Type estimated time per task suite in seconds (press enter to exit): ")

        if time_per_suite == "":
            break

        try:
            time_per_suite = int(time_per_suite)
            
        except ValueError:
            print("Please type a number \n")
            continue
        
        suites_per_hour = 60*60 / time_per_suite
        suggested_reward = 12 / suites_per_hour
        print(f"Suggested reward is ${suggested_reward} \n")


calculate_rewards()