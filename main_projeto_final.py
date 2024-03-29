from leitura_de_arquivos import processamento_dos_dados
import gurobipy as gp
from gurobipy import GRB

try:
    rj,dj,pj,wj = processamento_dos_dados('instance.txt')
    
    m = gp.Model("mip1")

    print('rj:',rj)
    print('dj:',dj)
    print('pj:',pj)
    print('wj:',wj)

    var_atrasos = []
    var_terminos = []
    ordem = []
    volta_fantasma = []
    infinity = GRB.INFINITY

    
    #CRIAÇÃO DAS VARIÁVEIS BINÁRIAS QUE DEFINEM A ORDEM DOS PEDIDOS
    i=0
    aux = 1
    while(aux <=len(rj)): #Criação do nó fantasma
        decisao_ordem = m.addVar(vtype=GRB.BINARY, name='x'+str(0)+str(aux))
        ordem.append(decisao_ordem)
        aux+=1
    LinExpr = gp.LinExpr()
    while(i < len(rj)):
        LinExpr.add(ordem[-len(rj):][i], 1)
        i+=1
    m.addConstr(LinExpr == 1, 'Rs0') #Restrição do somatório das saídas em um nó fantasma == 1
    del LinExpr

    i = 1
    j = 0
    while(i <= len(rj)): #Criação dos nós das tarefas
        LinExpr = gp.LinExpr()
        while(j <= len(rj)):
            if(i != j):
                if(j==0):
                    volta = m.addVar(vtype=GRB.BINARY, name='x'+str(i)+str(j))
                    LinExpr.add(volta, 1)
                    volta_fantasma.append(volta)
                else:
                    decisao_ordem = m.addVar(vtype=GRB.BINARY, name='x'+str(i)+str(j))
                    ordem.append(decisao_ordem)
            j+=1
        aux=0
        while(aux < len(rj)-1):
            LinExpr.add(ordem[-(len(rj)-1):][aux], 1)
            aux+=1
        m.addConstr(LinExpr == 1, 'Rs'+str(i)) #Restrição do somatório das saídas em um nó de tarefas == 1
        del LinExpr
        j=0
        i+=1

    LinExpr = gp.LinExpr() 
    cont=0
    while(cont < len(volta_fantasma)):
        LinExpr.add(volta_fantasma[cont], 1) #RESTRIÇÕES DE VOLTA PARA O NÓ FANTASMA
        cont+=1
    m.addConstr(LinExpr == 1, 'Re0')
    
    i = 1                     
    j = 1
    aux=1
    while(i <= len(rj)):
        cont = 0
        arrayProvisorio = []
        LinExpr = gp.LinExpr()
        while(j <= len(ordem[-(len(ordem)-len(rj)):])):
            arrayProvisorio.append(ordem[-(len(ordem)-len(rj)):][j-1])
            if(aux==len(arrayProvisorio)):
                j+=(2*(len(rj)))-1
            else:
                j=j+len(rj)-1
        while(cont < len(arrayProvisorio)):
            LinExpr.add(arrayProvisorio[cont], 1)
            cont+=1
        if(i==len(rj)):
            LinExpr.add(ordem[0], 1)
            m.addConstr(LinExpr == 1, 'Re'+str(i))
        else:
            LinExpr.add(ordem[i], 1)
            m.addConstr(LinExpr == 1, 'Re'+str(i))
        i+=1
        j=i
        aux=i
        del arrayProvisorio
        del LinExpr
        
    
        
    #CRIAÇÃO DAS VARIÁVEIS INTEIRAS QUE DEFINEM AS RESTRIÇÕES DE TÉRMINO 
    i = 1
    var_terminos.append(m.addVar(ub=0, name='vy0')) #Término do nó fantasma (y0)
    while(i <= len(rj)):
        termino = m.addVar(ub=infinity, name ='vy'+str(i))
        termino.vType = GRB.INTEGER
        var_terminos.append(termino)
        i+=1
    
    #CRIAÇÃO DAS VARIÁVEIS INTEIRAS QUE DEFINEM AS RESTRIÇÕES DE ATRASO
    i = 1
    var_atrasos.append(m.addVar(ub=0, name='va0')) #atraso do nó fantasma (y0)
    while(i <= len(rj)):
        atraso = m.addVar(ub=infinity, name ='va'+str(i))
        atraso.vType = GRB.INTEGER
        var_atrasos.append(atraso)
        i+=1
    #CRIAÇÃO DAS RESTRIÇÕES DE TÉRMINO
    i = 1
    m.addConstr(var_terminos[0] == 0, 'y0')
    while(i <= len(rj)):
        m.addConstr(var_terminos[i] >= dj[i-1] + rj[i-1], 'y'+str(i))
        i+=1
    
    #CRIAÇÃO DAS RESTRIÇÕES DE ATRASO
    i = 1
    m.addConstr(var_atrasos[0] == 0, 'a0')

    while(i <= len(rj)):
        m.addConstr(var_atrasos[i] >= var_terminos[i] - pj[i-1], 'a'+str(i))
        m.addConstr(var_atrasos[i] >= 0, 'ca'+str(i))
        i+=1
    
    i = 1
    el = gp.LinExpr()
    while(i <= len(rj)):
        el.add(var_atrasos[i], wj[i-1])
        i+=1
    m.setObjective(el, GRB.MINIMIZE)

    #CRIAÇÃO DAS RESTRIÇÕES DE TÉRMINOS Yj >= Yi + dj - ((1 - Xij)M)
    i = 1
    j = 0
    cont = 0
    bigM = 1e5

    while(i <= len(rj)):
        aux = i-1
        j=0
        while(j < len(rj)+1):
            m.addConstr(var_terminos[i] >= var_terminos[j] + dj[i-1] - (1 - ordem[aux])*bigM, 'Y'+str(i))
            if(j+1==i):
                aux+=(2*(len(rj))-1) 
                j+=2 
            else:
                aux+=len(rj)-1
                j+=1
        i+=1
    
    
    
    m.optimize()
    #print(m.display())
   
        
    Grupos_Ordem = []
    i = 1
    arrayAux = []
    for v in m.getVars():
        if(v.varName[0]=='x'):
            arrayAux.append(v)

        if(len(arrayAux)!=0):
            if(i == len(rj)):
                Grupos_Ordem.append(arrayAux)
                del arrayAux
                arrayAux = []
                i=1
        
        i+=1
    ordemPrint = []
    for i in Grupos_Ordem:
        for j in i:
            if(j.x == 1.0):
                ordemPrint.append(j.varName[-1])
    del Grupos_Ordem
                
    i = 0
    aux = 0
    Grupos_Ordem = []
    while(i < len(ordemPrint)):
        if(aux>=len(ordemPrint)):
            break
        if(i==0):
            print('Melhor ciclo escalonado de tarefas: ', 0, end='')
            Grupos_Ordem.append(0)
        print(' ->', ordemPrint[i], end='')
        Grupos_Ordem.append(ordemPrint[i])
        i=int(ordemPrint[i])
        aux+=1
    print('')

    
    i=1
    aux=1
    while(i <= len(rj)):
        print(str(i)+'ª Tarefa:', Grupos_Ordem[i], '| Dia ', aux, 'ao dia', aux+dj[int(Grupos_Ordem[i])-1]-1,'| Multa aplicada:', var_atrasos[int(Grupos_Ordem[i])].x*wj[int(Grupos_Ordem[i])-1], '|',
        var_atrasos[int(Grupos_Ordem[i])].x, 'dias atrasados ( Multa por dia:', wj[int(Grupos_Ordem[i])-1], ')')
        aux+=dj[int(Grupos_Ordem[i])-1]
        i+=1
    print('Multa Total: %g' % m.objVal)


#0 -> 5 -> 1 -> 6 -> 3 -> 2 -> 7 -> 4 -> 0

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
    
