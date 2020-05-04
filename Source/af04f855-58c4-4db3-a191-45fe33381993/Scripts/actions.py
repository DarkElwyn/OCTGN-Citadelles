# -- coding: utf-8 --
import re
from datetime import datetime
import time

highlightColor = "#ffffff"

######################
####### EVENTS #######
######################

def OnCounterChanged(args):
	counter = args.counter
	if counter.value < 0 :
		counter.value = 0
	if "Quartiers_construits" in counter.name and not args.scripted:
		counter.value = args.value

def OnCardsMoved(args):
	if args.player == me:
		for card in args.cards:
			# je joue une carte depuis ma main
			if args.fromGroups[0] == me.hand and args.toGroups[0] == table:
				# c'est un personnage, donc c'est le début de mon tour
				if isPersonnage(card):
					startMyTurn(card)
				# c'est un quartier, donc je dois le payer
				if isQuartier(card):
					buy(card)
			refreshBuildingCounter()

def OnCardDoubleClicked(args):
	card = args.card
	if isPersonnage(card):
		doActionPersonnages(card)
	if isCouronne(card):
		newKingTurn()
	if isQuartier(card):
		if playerIsRole(me, "Condottiere"):
			if canDestroy(card):
				destroy(card)

######################
####### SETUP  #######
######################	

def setup():
	mute()
	if iAmHost():
		setGlobalVariable("dateTimeDebut", time.mktime(datetime.now().timetuple()))
		whisper("(Je suis l'hôte)")
		
		notify("################################")
		notify("Pour jouer :\n")
		notify("- Mettre la couronne sur la table")
		notify("- Double cliquer sur la couronne pour lancer un nouveau tour de table")
		notify("- Glisser son personnage sur le plateau lorsque c'est son tour")
		notify("- Glisser un quartier sur le plateau pour l'acheter")
		notify("- Double cliquer sur son personnage pour activer son pouvoir\n")
		notify("Le premier joueur qui a construit 7 quartiers déclenche la fin de partie")
		notify("################################")
		
		createRangeCards(shared.quartiers, 10, 40, type="Quartier")
		shared.quartiers.shuffle()
		
		createRangeCards(shared.personnages, 1, 8, type="Personnage")
		shared.personnages.shuffle()
		
		for player in getPlayers():
			shared.quartiers.shuffle()
			for card in shared.quartiers.top(4):
				card.moveTo(player.hand)
		
		king = getPlayers()[hyperRnd(0, len(getPlayers())-1)]
		createRangeCards(king.hand, 100, 100, type="Token")
		table.create("00000001-0000-0093-0001-000000000101", -100, -300, persist=True).anchor = True
		notify("Sa majesté {} {} est courroné Roi".format(king, getKingSuffix()))

######################
####### UTILS  #######
######################
def hyperRnd(min, max):
	result = min
	for player in getPlayers():
		result = rnd(min, max)
	return result

def isPersonnage(card,x=0,y=0):
	if type(card) is list:
		card = card[0]
	return "Personnage" in card.type

def isCouronne(card,x=0,y=0):
	if type(card) is list:
		card = card[0]
	return "Couronne" in card.name

def isForge(card,x=0,y=0):
	if type(card) is list:
		card = card[0]
	return "Forge" in card.name

def isQuartier(card):
	return "Quartier" in card.type

def isNotMyCard(card):
	return card.controller != me

def getPlayerByRole(role):
	for card in table:
		if isPersonnage(card):
				if role in card.name:
					return card.controller
	return None

def playerIsRole(player, role):
	for card in table:
		if isPersonnage(card):
			if card.controller == player:
				if role in card.name:
					return True
	return False

def isLaboBuilt(cards,x=0,y=0):
	if isQuartier(cards[0]):
		return isQuartierBuiltForPlayer("Laboratoire", me)
	return False

def isObservatoireBuilt():
	return isQuartierBuiltForPlayer("Observatoire", me)

def isBibliothequeBuilt():
	return isQuartierBuiltForPlayer("Bibliothèque", me)

def isQuartierBuiltForPlayer(quartier, player):
	for card in table:
		if card.controller == player:
			if quartier in card.name:
				return True
	return False

def canDestroy(card):
	if "Donjon" in card.name:
		whisper("Les Donjons sont indestructibles")
		return False
	if card.controller.quartiers_construits >= 7:
		whisper("Impossible de détruire un quartier d'une cité complète")
		return False
	if playerIsRole(card.controller, "Evêque"):
		whisper("Dieu protège les quartiers de l'Evêque")
		return False
	return True

def canShowNewKingTurn(card,x,y):
	return isCouronne(card) and whoIsWinner() == False

def canShowCalculateScore(card,x,y):
	return isCouronne(card) and whoIsWinner() != False

def getKingSuffix():
	kingSuffix = ["XIV","XVI","IX","1er","le Bel","Capet","le Sage","le Gros","le Hardi","le Pieu","le Bon","le Long","le Lion","Dagobert","de France","de Bretagne","d'Artois","de Champagne","de Bourgogne","d'Anjou","Bonaparte","de Navarre"]
	return kingSuffix[hyperRnd(0, len(kingSuffix)-1)]

def doIAmDead(victime):
	for card in me.hand:
		if card.name in victime:
			card.orientation = 1
			whisper("Argh... L'Assassin vous a poignardé {}".format(me))
			whisper("Ne vous révélez pas pour l'instant")
			whisper("Ne jouez pas votre tour")
			whisper("Révélez vous en dernier")

def doActionAssassin(card):
	if "Assassin" in card.name:
		choiceList = ["Le Voleur", "Le Magicien", "Le Roi", "L'Evêque", "Le Marchand", "L'Architecte", "Le Condottiere"]
		colorsList = ['#78797e', '#78797e', '#d2982a', '#2862a3', '#43c02b', '#78797e', '#c0362d'] 
		choice = askChoice("Quel personnage assassiner ?", choiceList, colorsList)
		
		if choice > 0:
			notify("{} assassine {}".format(me, choiceList[choice-1]))
			setGlobalVariable("victimeAssassin", choiceList[choice-1])
			remoteCallAll("doIAmDead", [choiceList[choice-1]])

def doActionVoleur(card):
	if "Voleur" in card.name:
		choiceList = ["Le Magicien", "Le Roi", "L'Evêque", "Le Marchand", "L'Architecte", "Le Condottiere"]
		colorsList = ['#78797e', '#d2982a', '#2862a3', '#43c02b', '#78797e', '#c0362d']
		
		#on exclut la victime de l'assassin
		victimeAssassin = getGlobalVariable("victimeAssassin")
		victimeIndex = choiceList.index(victimeAssassin)
		victimeCouleur = colorsList[victimeIndex]
		
		choiceList.remove(victimeAssassin)
		colorsList.remove(victimeCouleur)
		
		choice = askChoice("Quel personnage voler ?", choiceList, colorsList)
		
		if choice > 0:
			notify("Le Voleur {} volera  {}".format(me, choiceList[choice-1]))
			setGlobalVariable("victimeVoleur", choiceList[choice-1])

def doActionMagicien(card):
	if "Magicien" in card.name:
		mute()
		choiceList = ["Echanger sa main avec un autre joueur", "Remplacer des cartes de sa main"]
		colorsList = ['#601f85', '#5daa18'] 
		choice = askChoice("Quel tour de magie réaliser ?", choiceList, colorsList)
		
		if choice == 1:
			choiceListPlayers = map(lambda player : player.name, getPlayers())
			colorsListPlayers = map(lambda player : player.color, getPlayers())
			choicePlayer = askChoice("Avec qui échanger sa main ?", choiceListPlayers, colorsListPlayers)
			
			if choicePlayer > 0:
				notify("Abracadabra ! {} échange sa main avec {}".format(me, Player(choicePlayer)))
				
				myCards = [] # échange en 3 coups
				for card in me.hand:
					myCards.append(card)
				
				for card in Player(choicePlayer).hand:
					card.moveTo(me.hand)
				
				for card in myCards:
					card.moveTo(Player(choicePlayer).hand)
			
		if choice == 2:
			dialog = cardDlg(me.hand)
			dialog.title = "Choisir des quartier à défausser :"
			dialog.max = 100
			cardsToReplace = dialog.show()
			
			if cardsToReplace:
				shared.quartiers.shuffle()
				for card in shared.quartiers.top(len(cardsToReplace)):
					card.moveTo(me.hand)
				
				for card in cardsToReplace:
					card.moveTo(shared.quartiers)
				shared.quartiers.shuffle()
				
				notify("Shazam ! {} remplace {} cartes de sa main".format(me, len(cardsToReplace)))

def doActionRoi(card):
	mute()
	if "Roi" in card.name:
		notify("Vive le nouveau Roi : {} {}".format(me, getKingSuffix()))
		#le Roi prend le controlle de la couronne
		for card in table:
			if isCouronne(card):
				card.controller = me
				break
		
		gain = countCardOfColourOnBoard("Jaune")
		me.Or += gain
		notify("Le Roi {} collecte la capitation et gagne {} pièce{} d'or".format(me, str(gain), pluriel(gain)))

def doActionEveque(card):
	mute()
	if "Evêque" in card.name:
		gain = countCardOfColourOnBoard("Bleu")
		me.Or += gain
		notify("L'Evêque {} collecte la dime et gagne {} pièce{} d'or".format(me, str(gain), pluriel(gain)))

def doActionMarchand(card):
	mute()
	if "Marchand" in card.name:
		gain = countCardOfColourOnBoard("Vert") + 1
		me.Or += gain
		notify("Le Marchand {} collecte la gabelle et gagne {} pièce{} d'or".format(me, str(gain), pluriel(gain)))

def doActionCondo(card):
	mute()
	if "Condottiere" in card.name:
		gain = countCardOfColourOnBoard("Rouge")
		me.Or += gain
		notify("Le Condottiere {} collecte la taille et gagne {} pièce{} d'or".format(me, str(gain), pluriel(gain)))
		whisper("Rappel : Double clic sur un Quartier ennemi pour le détruire")

def countCardOfColourOnBoard(color):
	count = 0
	for card in table:
		if card.controller == me:
			if card.couleur == color or card.name == "Ecole de Magie":
				count += 1
	return count

def doActionArchitecte(card):
	mute()
	if "Architecte" in card.name:
		shared.quartiers.shuffle()
		for card in shared.quartiers.top(2):
			card.moveTo(me.hand)
		
		notify("L'Architecte {} prends 2 Quartiers".format(me))

def doActionForge(card,x=0,y=0):
	mute()
	if me.Or >= 2:
		me.Or -= 2
		shared.Quartiers.shuffle()
		for card in shared.Quartiers.top(3):
			card.moveTo(me.hand)
		notify("{} forge 3 plans de Quartiers".format(me))
	else:
		whisper("Pas assez d'Or pour forger.")

def doActionLabo(card,x=0,y=0):
	mute()
	card.moveTo(shared.quartiers)
	shared.quartiers.shuffle()
	me.Or += 2
	notify("{} dissout le plan d'un Quartier dans une potion de feu grégeois, et gagne 2 Or".format(me))

def doActionCimetiere(card):
	if isQuartierBuiltForPlayer("Cimetière", me):
		if not playerIsRole(me, "Condottiere"):
			if me.Or >= 1:
				dialog = cardDlg([card])
				dialog.title = "Cimetière : Payer 1 Or pour prendre cette carte dans ma main ? "
				dialog.min = 1
				dialog.max = 1
				cardsToRessucitate = dialog.show()
				
				if cardsToRessucitate:
					cardsToRessucitate[0].moveTo(me.hand)
					me.Or -= 1
					notify("{} récupère le plan de {} dans le Cimetière".format(me, card.name,))

def iAmHost():
	return me._id == 1

def remoteCallAll(functionName, params = []):
	mute()
	for p in getPlayers():
		remoteCall(p,functionName,params)

def notifyBarAll(message, color = "#FF0000"):
	message += " " * 500
	remoteCallAll("notifyBar",[color,message])
	notify(message)

def createRangeCards(destination, fromID, toID, type=""):
	for i in range(fromID, toID+1):
		card = destination.create("00000001-0000-0093-0001-000000000{}".format(str(i).zfill(3)))
		if card:
			card.type = type
			if card.quantite and card.quantite > 1:
				for j in range(eval(card.quantite)-1):
					additionalCard = destination.create("00000001-0000-0093-0001-000000000{}".format(str(i).zfill(3)))
					additionalCard.type = type

def printGameDuration(a=0,b=0,c=0):
	begin = datetime.fromtimestamp(eval(getGlobalVariable("dateTimeDebut")))
	duration = datetime.utcfromtimestamp((datetime.now() - begin).total_seconds())
	notify("La partie a durée {}".format(duration.strftime('%Hh%Mmin')))

def getNextPlayer():
	return Player((me._id % len(getPlayers()))+1)

def buy(card):
	mute()
	prix = eval(card.prix)
	if prix <= me.Or:
		me.Or -= prix
	else:
		whisper("Impossible d'acheter ce Quartier car elle est trop chère")
		card.moveTo(me.hand)

def refreshBuildingCounter(a=0):
	count = 0
	for card in table:
		if card.controller == me:
			if isQuartier(card):
				count += 1
	me.quartiers_construits = count
	checkWinner()

def checkWinner():
	winner = whoIsWinner()
	if winner and getGlobalVariable("winnerFound") == "None":
		notifyBarAll("{} a construit 7 batiments, c'est donc le dernier tour !".format(winner))
		setGlobalVariable("winnerFound", winner._id)

def whoIsWinner():
	end = False
	for player in getPlayers():
		if player.quartiers_construits >= 7:
			end = player
	return end

def destroy(card):
	bonusMuraille = 0
	if isQuartierBuiltForPlayer("Grande Muraille", card.controller):
		bonusMuraille = 1

	prixAPayer = eval(card.prix)-1+bonusMuraille
	choiceList = ["Oui, payer {} Or".format(str(prixAPayer)), 'Non merci']
	colorsList = ['#d4ac0d', '#2471a3'] 
	choice = askChoice("Détruire le {} de {} ?".format(card.name, card.controller), choiceList, colorsList)
	
	if choice == 1:
		if me.Or >= prixAPayer:
			me.Or -= prixAPayer
			notify("BOOM ! Les canons du Condottiere {} ont détruit le {} de {}".format(me, card.name, card.controller))
			card.moveTo(shared.Quartiers)
			shared.Quartiers.shuffle()
			remoteCall(card.controller,"refreshBuildingCounter", [])
			remoteCallAll("doActionCimetiere", [card])
		else:
			whisper("Impossible de payer la destruction")

def colorPriceSort(card):
	return (ord(card.couleur[0])+ord(card.couleur[0]))*10+eval(card.prix)

def pluriel(count):
	if count > 1:
		return 's'
	return ''

def calculateMyScore():
	score = 0
	summary = "-----------------------------------------"
	summary = "\nCalcul des points de {} :\n".format(me)
	
	couleurs = {"Bleu":0, "Jaune":0, "Rouge":0, "Vert": 0, "Violet":0}
	
	mesQuartiers = [card for card in table if isQuartier(card) and card.controller == me]
	for quartier in mesQuartiers:
		score += eval(quartier.prix)
		couleurs[quartier.couleur] =1
	summary += "\nBase : Coût des Quartiers = {} points".format(score)
	
	for quartier in mesQuartiers:
		if "Dracoport" in quartier.name or "Université" in quartier.name:
			score += 2
			summary += "\nBonus : {} = 2 points supplémentaires".format(quartier.name)
	
	colorsSum = sum(couleurs.values())
	if colorsSum == 5 or (colorsSum == 4 and isQuartierBuiltForPlayer("Cour des Miracles", me)):
		score += 3
		summary += "\nBonus : Arc-en-ciel = 3 points"
	
	if me.quartiers_construits >= 7:
		score += 2
		summary += "\nBonus : Cité terminée = 2 points"
	
	if me._id == eval(getGlobalVariable("winnerFound")):
		score += 2
		summary += "\nBonus : Première cité terminée = 2 points"
	
	if isQuartierBuiltForPlayer("Trésor Impérial", me):
		score += me.Or
		summary += "\nBonus : Trésor Impérial = {} points".format(str(me.Or))
	
	if isQuartierBuiltForPlayer("Salle des Cartes", me):
		score += len(me.hand)
		summary += "\nBonus : Salle des Carte = {} points".format(str(len(me.hand)))
	
	summary += "\n\nLe score total de {} est de {} points".format(me, score)
	notify(summary)

def rotate(card,x=0,y=0):
	if card.orientation == 0:
		card.orientation = 1
	else:
		card.orientation = 0

def flip(card,x=0,y=0):
	if card.isFaceUp == False:
		card.orientation = True
	else:
		card.orientation = False

######################
#### PILE ACTIONS ####
######################

def shuffle(group, x = 0, y = 0):
    mute()
    group.shuffle()
    notify("{} mélange sa {}.".format(me, group.name))

######################
#### HAND ACTIONS ####
######################

#######################
#### TABLE ACTIONS ####
#######################

def arrange(group = (), x = 0, y = 0):
	myCards = [card for card in table if isQuartier(card) and card.controller == me]
	myCards.sort(key=lambda x:x.position[0])
	
	if myCards:
		x, y = myCards[0].position
		
		myCards.sort(key=colorPriceSort)
		inc = 0
		for card in myCards:
			card.moveToTable(x+inc, y)
			card.index = inc
			inc += 30

def startMyTurn(card,b=0,c=0):
	notify("{} commence son tour".format(me))
	
	#check si on se fait voler
	victimeVoleur = getGlobalVariable("victimeVoleur")
	if card.name in victimeVoleur:
		notify("Oh non ! Le {} {} se fait voler tout son tésor ({} Or) !".format(card.name, me, me.Or))
		voleur = getPlayerByRole("Voleur")
		voleur.Or += me.Or
		me.Or = 0
	#check si on se fait tuer
	victimeAssassin = getGlobalVariable("victimeAssassin")
	if card.name in victimeAssassin:
		notify("Le cadavre de {} est retrouvé, ensanglanté".format(me))
		notify("Il portait les habits du {}".format(card.name))
		whisper("Passez votre tour")
		return
	
	parmi = 2
	if isObservatoireBuilt():
		parmi = 3
	
	choisir = 1
	pluriel = ''
	if isBibliothequeBuilt():
		choisir = parmi
		pluriel = 's'
	
	choiceList = ["Prendre 2 Pièces d'Or", 'Choisir {} Quartier{} parmi {}'.format(str(choisir), pluriel, str(parmi))]
	colorsList = ['#d4ac0d', '#2471a3'] 
	choice = askChoice("Je commence mon tour, que faire ?", choiceList, colorsList)
	
	if choice == 1:
		me.Or += 2
	if choice == 2:
		shared.quartiers.shuffle()
		dialog = cardDlg(shared.quartiers.top(parmi))
		dialog.title = "Quel quartier choisir ?"
		dialog.min = choisir
		dialog.max = choisir
		
		cardsSelected = dialog.show()
		if cardsSelected:
			for card in cardsSelected:
				card.moveTo(me.hand)

def newKingTurn(a=0,b=0,c=0):
	if whoIsWinner() != False:
		printGameDuration()
		notify("La partie est terminée, calcul des scores:")
		remoteCallAll("calculateMyScore", [])
		return

	for card in table:
		if isPersonnage(card) or "Ghost" in card.type:
			card.moveTo(shared.personnages)

	visible = [ 0, 2, 2, 2, 2, 1, 0, 0 ]
	shared.personnages.shuffle()
	
	i = 0
	for card in shared.personnages.top(visible[len(getPlayers())]):
		card.moveToTable(-65-140+i*(140*2), -100, False)
		card.type = "Ghost"
		i += 1
	
	hidden = shared.personnages.top()
	hidden.moveToTable(-65, -100, True)
	hidden.type = "Ghost"
	
	setGlobalVariable("victimeVoleur", "None")
	setGlobalVariable("victimeAssassin", "None")
	
	pickOnePersonnage()

def pickOnePersonnage(a=0,b=0,c=0):
	dialog = cardDlg(shared.personnages)
	dialog.title = "Sélectionner 1 personnage"
	dialog.min = 1
	dialog.max = 1
	
	cardsSelected = dialog.show()
	if cardsSelected:
		notify("{} a choisi un personnage".format(me))
		for card in cardsSelected:
			card.moveTo(me.hand)
			card.type = "Personnage"
		
		if len(shared.personnages) >= 2:
			whisper("Le prochain à choisir un personnage est {}".format(getNextPlayer()))
			remoteCall(getNextPlayer(), "pickOnePersonnage", [])
		else:
			notify("Tous les joueurs ont choisi un personnage")
			notify("Le Roi doit appeler les personnages dans l'ordre")
	else:
		whisper("Aucun personnage selectionné >.<")
		whisper("Pour choisir de nouveau : Clic droit sur la table > Oups... choisir mon personnage")

def doActionPersonnages(card,x=0,y=0):
	doActionAssassin(card)
	doActionVoleur(card)
	doActionMagicien(card)
	doActionRoi(card)
	doActionEveque(card)
	doActionMarchand(card)
	doActionCondo(card)
	doActionArchitecte(card)