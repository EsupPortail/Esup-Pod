from datetime import datetime


def calcul(parameters) :

    #id: Id of the video (int)
    #title: Title of the video (string)
    #view_count : count the views of the video (int)
    #view_count_year : Views during the last year)
    #date_added': upload date of the video(datetime)
    #days_on_platform: number of days on the platforme (int)
    #date_delete: scheduled date of suppression (datetime.date)
    #description: description of the video (string)
    #channel_count: count of the number of channel the video belong (int)
    #nb_fav: number of favorite the video belong (int)
    #nb_comment: amount of comment on the video (int)
    #duration_video': 'duration of the video (??)
    #type_video : Video type (string)
    #themes_video': themes of the video (array)
    #owner_video': owner of the video (string)
    #owner_video_additional: Additional owner of the video (string)
    #category_list: categories of the video (array)

    print(parameters)

    ########## code perso ##########
    #score pour la vue
    if (parameters['view_count'] > 10):
        vue_score= parameters['view_count']/5
    else:
        vue_score=0

    # score pour la durée
    if (int(datetime.strptime(parameters['duration_video'], '%H:%M:%S').time().strftime('%S')) > 10):
        duration_score = 0
    else:
        duration_score = 10

    #score les commentaires
    if (parameters['nb_comment'] >= 2):
        score_commentaire=2
    else :
        score_commentaire=0

    #score favoris
    if (parameters['nb_fav'] >= 1):
        score_fav = 1
    else :
        score_fav = 0


    return (vue_score + duration_score + score_commentaire + score_fav)