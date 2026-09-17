from app.connectors.slack import SlackClient

def main():
    client=SlackClient()
    print(client.api('auth.test'))
if __name__=='__main__': main()
