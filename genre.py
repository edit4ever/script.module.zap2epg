# genre Mapping of tv shows found in zap2it website
################################################################################
#   This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################
genreCount = []

def countGenres():
    global genreCount
    return genreCount

def genreSort(edict, userSelectedGenre, useHex):
    global genreCount
    genreList = []
    updatedgenreList = []
    EPgenre = edict['epgenres']

    if userSelectedGenre == '1':          #User selected 'Simple'
        for g in EPgenre:
            if g != "Comedy":
                genreList.append(g)
        if not set(['movie','Movie','Movies','movies']).isdisjoint(genreList):
            genreList.insert(0, "Movie / Drama")
        if not set(['News']).isdisjoint(genreList):
            genreList.insert(0, "News / Current Affairs")
        if not set(['Game show']).isdisjoint(genreList):
            genreList.insert(0, "Game show / Quiz / Contest")
        if not set(['Law']).isdisjoint(genreList):
            genreList.insert(0, "Show / Game show")
        if not set(['Art','Culture']).isdisjoint(genreList):
            genreList.insert(0, "Arts / Culture (without music)")
        if not set(['Entertainment']).isdisjoint(genreList):
            genreList.insert(0, "Popular culture / Traditional Arts")
        if not set(['Politics','Social','Public affairs']).isdisjoint(genreList):
            genreList.insert(0, "Social / Political issues / Economics")
        if not set(['Education','Science']).isdisjoint(genreList):
            genreList.insert(0, "Education / Science / Factual topics")
        if not set(['How-to']).isdisjoint(genreList):
            genreList.insert(0, "Leisure hobbies")
        if not set(['Travel']).isdisjoint(genreList):
            genreList.insert(0, "Tourism / Travel")
        if not set(['Sitcom']).isdisjoint(genreList):
            genreList.insert(0, "Variety show")
        if not set(['Talk']).isdisjoint(genreList):
            genreList.insert(0, "Talk show")
        if not set(['Children']).isdisjoint(genreList):
            genreList.insert(0, "Children's / Youth programs")
        if not set(['Animated']).isdisjoint(genreList):
            genreList.insert(0, "Cartoons / Puppets")
        if not set(['Music']).isdisjoint(genreList):
            genreList.insert(0, "Music / Ballet / Dance")

        return genreList

    if userSelectedGenre == '2':          #User selected 'FULL' epg
        
        for g in EPgenre:
            genreList.append(g)

        #make each element lowercase, romve all spaces and any 's' at the end   
        genreList = list(map(lambda x: x.lower().replace(" ", ""), genreList))
        if (len(genreList) > 0 and genreList[0] != ''):
            genreList = list(map(lambda x: x[0:-1] if x[-1] == 's' else x, genreList))
        desc = f'{edict["epdesc"]} {edict["eptitle"]} {edict["epshow"]} {edict["epdesc"]}' 
        desc = desc.lower()

        #Movies   
        # TVHeadend Docs: https://github.com/tvheadend/tvheadend/blob/master/src/epg.c#L1775 line 1775    
        # Kodi Docs: https://github.com/xbmc/xbmc/blob/cda8e8c37190881fab4ea972d0d17cb54d5618d8/xbmc/addons/kodi-dev-kit/include/kodi/c-api/addon-instance/pvr/pvr_epg.h#L63 line 63
        # Look in the strings.po for the language selected to determine the text that will be displayed inside KODi for each code
        if not set(['movie']).isdisjoint(genreList):
            if not set(['adultsonly','erotic','gay/lesbian','lgbtq']).isdisjoint(genreList):
                updatedgenreList.append(["Adult movie","0x18"][useHex])                                           #Adult movie                    0x18
                genreCount.append("Adult movie")   
            elif not set(['detective','thriller','crime','crimedrama','mystery']).isdisjoint(genreList):
                updatedgenreList.append(["Detective/Thriller","0x11"][useHex])                                    #Detectivc/Thriller             0x11
                genreCount.append("Detective/Thriller")
            elif not set(['sciencefiction','fantasy','horror','paranormal']).isdisjoint(genreList):
                updatedgenreList.append(["Science fiction/Fantasy/Horror","0x13"][useHex])                        #Science Fiction/Fantasy/Horror 0x13
                genreCount.append("Science fiction/Fantasy/Horror")
            elif not set(['comedy','comedydrama','darkcomedy']).isdisjoint(genreList):
                updatedgenreList.append(["Comedy","0x14"][useHex])                                               #Comedy                         0x14
                genreCount.append("Comedy")
            elif not set(['western','war','military']).isdisjoint(genreList):
                updatedgenreList.append(["Adventure/Western/War","0x12"][useHex])                                #Adventure/Western/War          0x12
                genreCount.append("Adventure/Western/War")
            elif not set(['soap','melodrama','folkloric','music','musical','musicalcomedy']).isdisjoint(genreList):
                updatedgenreList.append(["Soap/Melodrama/Folkloric","0x15"][useHex])                             #Soap/Melodrama/Folkloric       0x15
                genreCount.append("Soap/Melodrama/Folkloric")
            elif not set(['romance','romanticcomedy']).isdisjoint(genreList):
                updatedgenreList.append(["Romance","0x16"][useHex])                                              #Romance                        0x16
                genreCount.append("Romance")
            elif not set(['serious','classical','religious','historicaldrama','biography','documentary','docudrama']).isdisjoint(genreList):
                updatedgenreList.append(["Serious/Classical/Religious/Historical movie/Drama","0x17"][useHex])   #Serious/Classical/Religious/Historical Movie/Drama     0x17
                genreCount.append("Serious/Classical/Religious/Historical movie/Drama")
            elif not set(['adventure']).isdisjoint(genreList):
                updatedgenreList.append(["Adventure/Western/War","0x12"][useHex])                                #Adventure/Western/War          0x12
                genreCount.append("Adventure/Western/War")
            else:
                updatedgenreList.append(["Movie / drama","0x10"][useHex])                                        #Movie/Drana                    0x10
                genreCount.append("Movie / drama")

        #Adult TV Shows
        elif not set(['adultsonly','erotic','Gay/lesbian','LGBTQ']).isdisjoint(genreList):
                updatedgenreList.append(["Adult movie","0xF8"][useHex])                                          #Adult Show                     0xF8
                genreCount.append("Adult movie")

        #Children Programming
        elif not set(['children','youth']).isdisjoint(genreList):
            if edict['eprating'] == 'TV-Y':
                updatedgenreList.append(["Pre-school children's programs","0x51"][useHex])                       #Pre-school Children's Programmes           0x51
                genreCount.append("Pre-school children's programs")
            elif edict['eprating'] == 'TV-Y7':
                updatedgenreList.append(["Entertainment programs for 6 to 14","0x52"][useHex])                   #Entertainment Programmes for 6 to 14       0x52
                genreCount.append("Entertainment programs for 6 to 14")
            elif edict['eprating'] == 'TV-G':
                updatedgenreList.append(["Entertainment programs for 10 to 16","0x53"][useHex])                  #Entertainment Programmes for 10 to 16      0x53                                      
                genreCount.append("Entertainment programs for 10 to 16")
            elif not set(['informational','educational','science','technology']).isdisjoint(genreList):
                updatedgenreList.append(["Informational/Educational/School programs","0x54"][useHex])            #Informational/Educational/School Programme 0x54        
                genreCount.append("Informational/Educational/School programs")
            elif not set(['anime','animated']).isdisjoint(genreList):
                updatedgenreList.append(["Cartoons/Puppets","0x55"][useHex])                                     #Cartoons/Puppets                           0x55 
                genreCount.append("Cartoons/Puppets")
            else: 
                updatedgenreList.append(["Children's / Youth programs","0x50"][useHex])                          #Children's/Youth Programs                  0x50
                genreCount.append("Children's / Youth programs")

        #MLeisure/Hobbies
        elif not set(['advertisement','archery','auto','bodybuilding','consumer','cooking','exercise','fishing','fitness',
                'fitness&amp;health','gardening','handicraft','health','hobby','homeimprovement','house/garden','how-to','hunting',
                'motoring','outdoor','selfimprovement','shopping','tourism','travel']).isdisjoint(genreList):

            if not set(['tourism','travel']).isdisjoint(genreList):
                updatedgenreList.append(["Tourism / Travel","0xA1"][useHex])                                     #Tourism/Travel             0xA1
                genreCount.append("Tourism / Travel")
            elif not set(['handicraft','homeimprovement','house/garden','how-to']).isdisjoint(genreList):
                updatedgenreList.append(["Handicraft","0xA2"][useHex])                                           #Handicraft                 0xA2         
                genreCount.append("Handicraft")
            elif not set(['motoring','auto']).isdisjoint(genreList):
                updatedgenreList.append(["Motoring","0xA3"][useHex])                                             #Motoring                   0xA3
                genreCount.append("Motoring")
            elif not set(['fitnes','health','fitness&amp;health','selfimprovement','bodybuilding','exercise']).isdisjoint(genreList):
                updatedgenreList.append(["Fitness and health","0xA4"][useHex])                                   #Fitness & Health           0xA4
                genreCount.append("Fitness and health")
            elif not set(['cooking']).isdisjoint(genreList):
                updatedgenreList.append(["Cooking","0xA5"][useHex])                                              #Cooking                    0xA5
                genreCount.append("Cooking")
            elif not set(['advertisement','shopping','consumer']).isdisjoint(genreList):
                updatedgenreList.append(["Advertisement / Shopping","0xA6"][useHex])                             #Advertisement/Shopping     0xA6
                genreCount.append("Advertisement / Shopping")
            elif not set(['gardening']).isdisjoint(genreList):
                updatedgenreList.append(["Gardening","0xA7"][useHex])                                            #Gardening                  0xA7
                genreCount.append("Gardening")
            else: 
                updatedgenreList.append(["Leisure hobbies","0xA0"][useHex])                                      #Leisure/Hobbies            0xA0
                genreCount.append("Leisure hobbies")

        #News 
        elif not set(['currentaffair','documentary','interview','news','newsmagazine']).isdisjoint(genreList):
            
            if not set(['weather']).isdisjoint(genreList):
                updatedgenreList.append(["News/Weather report","0x21"][useHex])                                  #News/Weather Report            0x21
                genreCount.append("News/Weather report")
            elif not set(['newsmagazine']).isdisjoint(genreList):
                updatedgenreList.append(["News magazine","0x22"][useHex])                                        #News Magazine                  0x22         
                genreCount.append("News magazine")
            elif not set(['documentary']).isdisjoint(genreList):
                updatedgenreList.append(["Documentary","0x23"][useHex])                                          #Documentary                    0x23
                genreCount.append("Documentary")
            elif not set(['discussion','interview','debate']).isdisjoint(genreList):
                updatedgenreList.append(["Discussion/Interview/Debate","0x24"][useHex])                          #Discussion/Interview/Debate    0x24
                genreCount.append("Discussion/Interview/Debate")
            else:
                updatedgenreList.append(["News/Current Affairs","0x20"][useHex])                                 #News/Current Affair            0x20
                genreCount.append("News/Current Affairs")

        #Sports        
        elif not set(['actionsport','australianrulesfootball','autoracing','baseball','basketball','beachvolleyball','billiard','bmxracing',
                'boatracing','bobsled','bowling','boxing','bullriding','cheerleading','cricket','cycling','diving','dragracing','equestrian',
                'esport','fencing','fieldhockey','figureskating','fishing','football','footvolley','golf','gymnastic','hockey','horse','horseracing',
                'karate','lacrosse','martialart','mixedmartialart','motorcycle','motorcycleracing','motorsport','multisportevent','olympic',
                'paralympic','pickleball','prowrestling','racing','rodeo','rugby','rugbyleague','running','sailing','skating','skiing',
                'snowboarding','soccer','softball','squash','superbowl','surfing','swimming','tabletennis','tennis','track/field','volleyball',
                'waterpolo','watersport','weightlifting','wintersport','worldcup','wrestling']).isdisjoint(genreList):
            if not set(['documentary','sportstalk']).isdisjoint(genreList):
                updatedgenreList.append(["Sports magazines","0x42"][useHex])                                     #Sports magazines                                   0x42
                genreCount.append("Sports magazines")
            elif not set(['final','superbowl','worldcup','olympic','paralympic']).isdisjoint(genreList):
                updatedgenreList.append(["Special events (Olympic Games, World Cup, etc.)","0x41"][useHex])      #Special events (Olympic Games, World Cup, etc.)    0x41
                genreCount.append("Special events (Olympic Games, World Cup, etc.")
            elif not set(['football','soccer','australianrulesfootball']).isdisjoint(genreList):
                updatedgenreList.append(["Football/Soccer","0x43"][useHex])                                      #Football/Soccer                                    0x43
                genreCount.append("Football/Soccer")
            elif not set(['tabletennis','tennis','squash']).isdisjoint(genreList):
                updatedgenreList.append(["Tennis/Squash","0x44"][useHex])                                        #Tennis/Squash                                      0x44           
                genreCount.append("Tennis/Squash")
            elif not set(['basketball','hockey','baseball','softball','gymnastics','volleyball','track/field','fieldhockey',
                    'lacrosse','rugby','cricket','fieldhockey']).isdisjoint(genreList):
                updatedgenreList.append(["Team sports (excluding football)","0x45"][useHex])                     #Team sports (excluding football)                   0x45
                genreCount.append("Team sports (excluding football)")
            elif not set(['running','snowboarding','wrestling','cycling']).isdisjoint(genreList):
                updatedgenreList.append(["Athletics","0x46"][useHex])                                            #Athletics                                          0x46
                genreCount.append("Athletics")
            elif not set(['autoracing','dragracing','motorcycle','motorcycleracing','motorsport']).isdisjoint(genreList):
                updatedgenreList.append(["Motor sport","0x47"][useHex])                                          #Motor sports                                       0x47
                genreCount.append("Motor sport")
            elif not set(['bmxracing','boatracing','diving','fishing','sailing','surfing','swimming','waterpolo','watersport']).isdisjoint(genreList):
                updatedgenreList.append(["Water sport","0x48"][useHex])                                          #Water sport                                        0x48
                genreCount.append("Water sport")
            elif not set(['wintersport','skiing','bobsled','figureskating','skating','snowboarding']).isdisjoint(genreList):
                updatedgenreList.append(["Winter sports","0x49"][useHex])                                        #Winter sports                                      0x49
                genreCount.append("Winter sports")
            elif not set(['horse','equestrian','horseracing','rodeo','bullriding']).isdisjoint(genreList):
                updatedgenreList.append(["Equestrian","0x4A"][useHex])                                           #Equestrian                                         0x4A
                genreCount.append("Equestrian")
            elif not set(['martialart','mixedmartialart','karate']).isdisjoint(genreList):
                updatedgenreList.append(["Martial sports","0x4B"][useHex])                                       #Martial sports                                     0x4B
                genreCount.append("Martial sports")
            else:
                updatedgenreList.append(["Sports","0x40"][useHex])                                               #Sports                                             0x40
                genreCount.append("Sports")

        #Show
        elif not set(['competition','competitionreality','contest','gameshow','quiz','reality','talk','talkshow','variety',
                'varietyshow']).isdisjoint(genreList):
            if not set(['gameshow','quiz','contest']).isdisjoint(genreList):
                updatedgenreList.append(["Game show/Quiz/Contest","0x31"][useHex])                               #Game show/Quiz/Contest             0x31
                genreCount.append("Game show/Quiz/Contest")
            elif not set(['variety','varietyshow','competition','competitionreality','reality']).isdisjoint(genreList):
                updatedgenreList.append(["Variety show","0x32"][useHex])                                         #Variety Show                       0x32              
                genreCount.append("Variety show")
            elif not set(['talk','talkshow']).isdisjoint(genreList):
                updatedgenreList.append(["Talk show","0x33"][useHex])                                            #Talk Show                          0x33
                genreCount.append("Talk show")
            else:
                updatedgenreList.append(["Show / Game show","0x30"][useHex])                                     #Show/Game Show                     0x30
                genreCount.append("Show / Game show")

        #Music/Ballet/Dance
        elif not set(['ballet','classicalmusic','dance','folk','jazz','music','musical','opera','pop','rock','traditionalmusic']).isdisjoint(genreList):
            if not set(['rock','pop']).isdisjoint(genreList):
                updatedgenreList.append(["Rock/Pop","0x61"][useHex])                                             #Rock/Pop                           0x61
                genreCount.append("Rock/Pop")
            elif not set(['serious','classicalmusic']).isdisjoint(genreList):
                updatedgenreList.append(["Serious music/Classical music","0x62"][useHex])                        #Seriouis/Classical Music           0x62      
                genreCount.append("Serious music/Classical music")
            elif not set(['folk','traditionalmusic']).isdisjoint(genreList):
                updatedgenreList.append(["Folk/Traditional music","0x63"][useHex])                               #Folk/Traditional Music             0x63
                genreCount.append("Folk/Traditional music")
            elif not set(['jazz']).isdisjoint(genreList):
                updatedgenreList.append(["Jazz","0x64"][useHex])                                                 #Jazz                               0x64
                genreCount.append("Jazz")
            elif not set(['musical','opera']).isdisjoint(genreList):
                updatedgenreList.append(["Musical/Opera","0x65"][useHex])                                        #Musical/Opera                      0x65
                genreCount.append("Musical/Opera")
            elif not set(['ballet']).isdisjoint(genreList):
                updatedgenreList.append(["Ballet","0x66"][useHex])                                               #Ballet                             0x66
                genreCount.append("Ballet")
            else:
                updatedgenreList.append(["Music / Ballet / Dance","0x60"][useHex])                               #Music/Ballet/Dance                 0x60
                genreCount.append("Music / Ballet / Dance")

        #Arts/Culture
        elif not set(['art','arts/craft','artsmagazine','broadcasting','cinema','culture','culturemagazine','experimentalfilm','fashion','film',
            'fineart','literature','newmedia','performingart','popularculture','pres','religion','religious','traditionalart','video']).isdisjoint(genreList):

            if not set(['performingart']).isdisjoint(genreList):
                updatedgenreList.append(["Performing arts","0x71"][useHex])                                      #Performing Arts                    0x71
                genreCount.append("Performing arts")
            elif not set(['fineart']).isdisjoint(genreList):
                updatedgenreList.append(["Fine arts","0x72"][useHex])                                            #Fine Arts                          0x72            
                genreCount.append("Fine arts")
            elif not set(['religion','religious']).isdisjoint(genreList):
                updatedgenreList.append(["Religion","0x73"][useHex])                                             #Religion                           0x73
                genreCount.append("Religion")
            elif not set(['popculture','traditionalart']).isdisjoint(genreList):
                updatedgenreList.append(["Popular culture/Traditional arts","0x74"][useHex])                     #Pop Culture/Traditional Arts       0x74
                genreCount.append("Popular culture/Traditional arts")
            elif not set(['literature']).isdisjoint(genreList):
                updatedgenreList.append(["Literature","0x75"][useHex])                                           #Literature                         0x75
                genreCount.append("Literature")
            elif not set(['film','cinema']).isdisjoint(genreList):
                updatedgenreList.append(["Film/Cinema","0x76"][useHex])                                          #Film/Cinema                        0x76        
                genreCount.append("Film/Cinema")
            elif not set(['experimentalfilm','video']).isdisjoint(genreList):
                updatedgenreList.append(["Experimental film/Video","0x77"][useHex])                              #Experimental Film/Video            0x77
                genreCount.append("Experimental film/Video")
            elif not set(['broadcasting','pres']).isdisjoint(genreList):
                updatedgenreList.append(["Broadcasting/Press","0x78"][useHex])                                   #Broadcasting/Press                 0x78
                genreCount.append("Broadcasting/Press")
            elif not set(['newmedia']).isdisjoint(genreList):
                updatedgenreList.append(["New media","0x79"][useHex])                                            #New Media                          0x79
                genreCount.append("New media")
            elif not set(['artmagazine','culturemagazine','magazine']).isdisjoint(genreList):
                updatedgenreList.append(["Arts magazines/Culture magazines","0x7A"][useHex])                     #Arts/Culture Magazine              0x7A
                genreCount.append("Arts magazines/Culture magazines")
            elif not set(['fashion']).isdisjoint(genreList):
                updatedgenreList.append(["Fashion","0x7B"][useHex])                                              #Fashion                            0x7B
                genreCount.append("Fashion")
            else:    
                updatedgenreList.append(["Arts / Culture (without music)","0x70"][useHex])                       #Arts/Culture                       0x70
                genreCount.append("Arts / Culture (without music)")

        #Social/Politics/Economics
        elif not set(['community','documentary','economic','magazine','politic','political','publicaffair',
                'remarkablepeople','report','social','socialadvisory']).isdisjoint(genreList):

            if not set(['magazine','report','documentary']).isdisjoint(genreList):
                updatedgenreList.append(["Magazines/Reports/Documentary","0x81"][useHex])                        #Magazines/Reports/Documentary      0x81
                genreCount.append("Magazines/Reports/Documentary")
            elif not set(['economic','socialadvisory']).isdisjoint(genreList):
                updatedgenreList.append(["Economics/Social advisory","0x82"][useHex])                            #Economics/Social Advisory          0x82            
                genreCount.append("Economics/Social advisory")
            elif not set(['remarkablepeople']).isdisjoint(genreList):
                updatedgenreList.append(["Remarkable people","0x83"][useHex])                                    #Remarkable People                  0x83
                genreCount.append("Remarkable people")
            else:
                updatedgenreList.append(["Social/Political issues/Economics","0x80"][useHex])                    #Social/Political/Economics         0x80
                genreCount.append("Social/Political issues/Economics")

        #MEducational/Science
        elif not set(['adulteducation','animal','dogshow','education','educational','environment','expedition','factual','foreigncountrie',
                'furthereducation','health','language','medical','medicine','naturalscience','nature','outdoor','physiology','psychology',
                'science','social','spiritualscience','technology']).isdisjoint(genreList):
            
            if not set(['nature','animal','environment','outdoor','dogshow']).isdisjoint(genreList):
                updatedgenreList.append(["Nature/Animals/Environment","0x91"][useHex])                           #Nature/Animals/Environment         0x91          
                genreCount.append("Nature/Animals/Environment")
            elif not set(['technology','naturalscience']).isdisjoint(genreList):
                updatedgenreList.append(["Technology/Natural sciences","0x92"][useHex])                          #Technology/Natural Sciences        0x92
                genreCount.append("Technology/Natural sciences")
            elif not set(['medicine','physiology','psychology','health','medical']).isdisjoint(genreList):
                updatedgenreList.append(["Medicine/Physiology/Psychology","0x93"][useHex])                       #Medicine/Physiology/Psychology     0x93
                genreCount.append("Medicine/Physiology/Psychology")
            elif not set(['foreigncountrie','expedition']).isdisjoint(genreList):
                updatedgenreList.append(["Foreign countries/Expeditions","0x94"][useHex])                        #Foreign Countries/Expeditions      0x94
                genreCount.append("Foreign countries/Expeditions")
            elif not set(['social','spiritualscience']).isdisjoint(genreList):
                updatedgenreList.append(["Social/Spiritual sciences","0x95"][useHex])                            #Social/Spiritual Sciences          0x95
                genreCount.append("Social/Spiritual sciences")
            elif not set(['furthereducation','adulteducation']).isdisjoint(genreList):
                updatedgenreList.append(["Further education","0x96"][useHex])                                    #Further Education                  0x96
                genreCount.append("Further education")
            elif not set(['language']).isdisjoint(genreList):
                updatedgenreList.append(["Languages","0x97"][useHex])                                            #Languages                          0x97
                genreCount.append("Languages")
            else:
                updatedgenreList.append(["Education / Science / Factual topics","0x90"][useHex])                 #Education/Science                  0x90
                genreCount.append("Education / Science / Factual topics")

        # TVHeadend does not recognize the non-movie genres below.  0xF# are user defined genres per the specification and TVH
        # does not use them.  Kodi does use these user defined values.  I could not figure out a way to pass the hex code to TVH
        # instead of the string to be recoginzed correctly.  When TVH is modified to accept a hex value for the genre we can then
        # use these codes to get correct EPG colored grids.  One color for movies with it's separate color and one for TV shows.

        elif not set(['crime','crimedrama','detective','mystery','thriller']).isdisjoint(genreList):
                updatedgenreList.append(["Detective/Thriller","0xF1"][useHex])                                   #Detective/Thriller                 0xF1
                genreCount.append("Detective/Thriller")

        elif not set(['fantasy','horror','paranormal','sciencefiction']).isdisjoint(genreList):
                updatedgenreList.append(["Science fiction/Fantasy/Horror","0xF3"][useHex])                       #Science Fiction/Fantasy/Horror     0xF3
                genreCount.append("Science fiction/Fantasy/Horror")

        elif not set(['western','war','military']).isdisjoint(genreList):
                updatedgenreList.append(["Adventure/Western/War","0xF2"][useHex])                                #Adventure/Western/War              0xF2
                genreCount.append("Adventure/Western/War")

        elif not set(['comedy','comedydrama','darkcomedy','sitcom']).isdisjoint(genreList):
                updatedgenreList.append(["Comedy","0xF4"][useHex])                                               #Comedy                             0xF4
                genreCount.append("Comedy")

        elif not set(['folk','folkloric','melodrama','music','musical','musicalcomedy','soap']).isdisjoint(genreList):
                updatedgenreList.append(["Soap/Melodrama/Folkloric","0xF5"][useHex])                             #Soap/Melodrama/Folkloric           0xF5
                genreCount.append("Soap/Melodrama/Folkloric")

        elif not set(['romance','romanticcomedy']).isdisjoint(genreList):
                updatedgenreList.append(["Romance","0xF6"][useHex])                                              #Romance                            0xF6
                genreCount.append("Romance")

        elif not set(['biography','classical','classicalreligion','docudrama','historical','historicaldrama','religion','serious']).isdisjoint(genreList):
                updatedgenreList.append(["Serious/Classical/Religious/Historical movie/Drama","0xF7"][useHex])  #Serious/Classical/Religion/Historical  0xF7
                genreCount.append("Serious/Classical/Religious/Historical movie/Drama")

        elif not set(['adventure']).isdisjoint(genreList):
                updatedgenreList.append(["Adventure/Western/War","0xF2"][useHex])                               #Adventure/Western/War              0xF2
                genreCount.append("Adventure/Western/War")

        elif not set(['drama']).isdisjoint(genreList):
                updatedgenreList.append(["Movie / Drama","0xF0"][useHex])                                       #Drama                              0xF0
                genreCount.append("Movie / Drama")

        return updatedgenreList

    if userSelectedGenre == '3':          #User selected 'original' epg tag
        for g in EPgenre:
            genreList.append(g)
        return genreList
