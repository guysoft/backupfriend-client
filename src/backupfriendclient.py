def run():
    import wx
    from backupfriend.main import main
    # Needed so pyinstaller will detect it needs this module
    import backupfriend.sub
    
    print(backupfriend)

    main()
    return

if __name__ == "__main__":
    run()
