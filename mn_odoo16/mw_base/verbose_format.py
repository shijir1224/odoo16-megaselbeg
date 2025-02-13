# -*- encoding: utf-8 -*-
##############################################################################
#
#   MANAGEWALL LLC
#
#
##############################################################################
def verbose_format(amount,currency=False):
    if type(amount) !=str :
        amount = str(amount)
    result = u''
    BUTARHAI = True
    i = 0
    #length = len(amount)
    # Форматаас болоод . -ын оронд , орсон байвал засна.
    stramount = amount.replace(',','.')
#    print "stramount ",stramount
    if '.' in amount:
        amount = stramount[:stramount.find('.')]
        subamount = stramount[stramount.find('.')+1:]
        if len(subamount)==1:
            subamount=str(int(subamount)*10)
#         print "subamount ",subamount
    else :
        amount = stramount
        subamount = u''
    length = len(amount)
    if length == 0 or float(amount) == 0:
        return ''
    place = 0
    try :
        while i < length :
            c = length - i
            if c % 3 == 0 :
                c -= 3
            else :
                while c % 3 != 0 :
                    c -= 1
            place = c / 3
            i1 = length - c
            tmp = amount[i:i1]
            j = 0
            if tmp == '000' :
                i = i1
                continue
            while j < len(tmp) :
                char = int(tmp[j])
                p = len(tmp) - j
                if char == 1 :
                    if p == 3 :
                        result += u'нэг зуун '
                    elif p == 2 :
                        result += u'арван '
                    elif p == 1 :
                        if len(result)==0:
                            result += u'нэг '
                        else:
                            result += u'нэгэн '
                elif char == 2 :
                    if p == 3 :
                        result += u'хоёр зуун '
                    elif p == 2 :
                        result += u'хорин '
                    elif p == 1 :
                        result += u'хоёр '
                elif char == 3 :
                    if p == 3 :
                        result += u'гурван зуун '
                    elif p == 2 :
                        result += u'гучин '
                    elif p == 1 :
                        result += u'гурван '
                elif char == 4 :
                    if p == 3 :
                        result += u'дөрвөн зуун '
                    elif p == 2 :
                        result += u'дөчин '
                    elif p == 1 :
                        result += u'дөрвөн '
                elif char == 5 :
                    if p == 3 :
                        result += u'таван зуун '
                    elif p == 2 :
                        result += u'тавин '
                    elif p == 1 :
                        result += u'таван '
                elif char == 6 :
                    if p == 3 :
                        result += u'зургаан зуун ' 
                    elif p == 2 :
                        result += u'жаран '
                    elif p == 1 :
                        result += u'зургаан '
                elif char == 7 :
                    if p == 3 :
                        result += u'долоон зуун '
                    elif p == 2 :
                        result += u'далан '
                    elif p == 1 :
                        result += u'долоон '
                elif char == 8 :
                    if p == 3 :
                        result += u'найман зуун '
                    elif p == 2 :
                        result += u'наян '
                    elif p == 1 :
                        result += u'найман '
                elif char == 9 :
                    if p == 3 :
                        result += u'есөн зуун '
                    elif p == 2 :
                        result += u'ерэн '
                    elif p == 1 :
                        result += u'есөн '
                
                j += 1
            # -------- end while j < len(tmp)
            if place == 3 :
                result += u'тэрбум '
            elif place == 2 :
                result += u'сая '
            elif place == 1 :
                result += u'мянга '
            i = i1
        # ---------- end while i < len(amount)
    except Exception as e  :
        return e
    if len(subamount) > 0 and float(subamount) > 0 :
        result2 = verbose_format(subamount,currency)
        BUTARHAI = False
        if currency:
            for currency_ids in currency:
                if currency_ids and currency_ids.name=='USD':
                    result2 = result2.replace(u'доллар', u'цент')
                    result += u' доллар %s' % result2
                elif currency_ids and currency_ids.name=='CNY':
                    result2 = result2.replace(u'юань', u'мо')
                    result += u' юань %s' % result2
                else:
                    result2 = result2.replace(u'төгрөг', u'мөнгө')
                    result += u' төгрөг %s' % result2
    if BUTARHAI:
        if currency:
            for currency_ids in currency:
                if currency_ids and currency_ids.name=='USD':
                    result += u' доллар'
                elif currency_ids and currency_ids.name=='CNY':
                    result += u' юань ' 
                else:
                    result += u' төгрөг'
            
    num = result
    if u"мянга  төгрөг" in num:
      result = num.replace(u"мянга  төгрөг",u"мянган  төгрөг")
    elif u"мянга  доллар" in num:
      result = num.replace(u"мянга  доллар",u"мянган  доллар")
    elif  u"мянга  юань" in num:
      result = num.replace(u"мянга  юань",u"мянган  юань")
    else:
      result = num

    return result


def verbose_format_china(amount,currency=False):
    if type(amount) !=str :
        amount = str(amount)
    result = u''
    BUTARHAI = True
    i = 0
    #length = len(amount)
    # Форматаас болоод . -ын оронд , орсон байвал засна.
    stramount = amount.replace(',','.')
#    print "stramount ",stramount
    if '.' in amount:
        amount = stramount[:stramount.find('.')]
        subamount = stramount[stramount.find('.')+1:]
        if len(subamount)==1:
            subamount=str(int(subamount)*10)
#         print "subamount ",subamount
    else :
        amount = stramount
        subamount = u''
    length = len(amount)
    if length == 0 or float(amount) == 0:
        return ''
    place = 0
    try :
        while i < length :
            c = length - i
            if c % 3 == 0 :
                c -= 3
            else :
                while c % 3 != 0 :
                    c -= 1
            place = c / 3
            i1 = length - c
            tmp = amount[i:i1]
            j = 0
            if tmp == '000' :
                i = i1
                continue
            while j < len(tmp) :
                char = int(tmp[j])
                p = len(tmp) - j
                if char == 1 :
                    if p == 3 :
                        result += u'壹佰 '
                    elif p == 2 :
                        result += u'拾 '
                    elif p == 1 :
                        if len(result)==0:
                            result += u'壹 '
                        else:
                            result += u'壹 '
                elif char == 2 :
                    if p == 3 :
                        result += u'贰佰 '
                    elif p == 2 :
                        result += u'贰拾 '
                    elif p == 1 :
                        result += u'贰 '
                elif char == 3 :
                    if p == 3 :
                        result += u'叁佰 '
                    elif p == 2 :
                        result += u'叁拾 '
                    elif p == 1 :
                        result += u'叁 '
                elif char == 4 :
                    if p == 3 :
                        result += u'肆佰 '
                    elif p == 2 :
                        result += u'肆拾 '
                    elif p == 1 :
                        result += u'肆 '
                elif char == 5 :
                    if p == 3 :
                        result += u'伍佰 '
                    elif p == 2 :
                        result += u'伍拾 '
                    elif p == 1 :
                        result += u'伍 '
                elif char == 6 :
                    if p == 3 :
                        result += u'陆佰 ' 
                    elif p == 2 :
                        result += u'陆拾 '
                    elif p == 1 :
                        result += u'陆 '
                elif char == 7 :
                    if p == 3 :
                        result += u'柒佰 '
                    elif p == 2 :
                        result += u'柒拾 '
                    elif p == 1 :
                        result += u'柒 '
                elif char == 8 :
                    if p == 3 :
                        result += u'捌佰 '
                    elif p == 2 :
                        result += u'捌拾 '
                    elif p == 1 :
                        result += u'捌 '
                elif char == 9 :
                    if p == 3 :
                        result += u'玖佰 '
                    elif p == 2 :
                        result += u'玖拾 '
                    elif p == 1 :
                        result += u'玖 '
                
                j += 1
            # -------- end while j < len(tmp)
            if place == 3 :
                result += u'拾亿 '
            elif place == 2 :
                result += u'亿 '
            elif place == 1 :
                result += u'仟 '
            i = i1
        # ---------- end while i < len(amount)
    except Exception as e  :
        return e
    if len(subamount) > 0 and float(subamount) > 0 :
        result2 = verbose_format(subamount,currency)
        BUTARHAI = False

        if currency:
            for currency_ids in currency:
                if currency_ids and currency_ids.name=='USD':
                    result2 = result2.replace(u'доллар', u'份')
                    result += u' 美元 %s' % result2
                elif currency_ids and currency_ids.name=='CNY':
                    result2 = result2.replace(u'юань', u'毛')
                    result += u' 元 %s' % result2
                else:
                    result2 = result2.replace(u'төгрөг', u'钱')
                    result += u' 蒙图 %s' % result2
    if BUTARHAI:
        if currency:
            for currency_ids in currency:
                if currency_ids and currency_ids.name=='USD':
                    result += u' 美元'
                elif currency_ids and currency_ids.name=='CNY':
                    result += u' 元 ' 
                else:
                    result += u' 蒙图'
            
    num = result
    if u"мянга  төгрөг" in num:
      result = num.replace(u"мянга  төгрөг",u"мянган  төгрөг")
    elif u"мянга  доллар" in num:
      result = num.replace(u"мянга  доллар",u"мянган  доллар")
    elif  u"мянга  юань" in num:
      result = num.replace(u"мянга  юань",u"мянган  юань")
    else:
      result = num

    return result

def num2cn2(number, traditional=False):
    second = False
    jj = 0
    print (number)
    if number%1!=0:
        jj = str(number).split('.')[1]
        second = num2cn(jj)
    ii = int(number // 1)
    first = num2cn(ii)
    return first, second

def num2cn(number, traditional=False): 
    """ 數字轉換成中文（簡體和繁體，目前支持到12位數值） :param number: :param traditional: :return: """
    if traditional: 
        chinese_num = {0: '零', 1: '壹', 2: '貳', 3: '叄', 4: '肆', 5: '伍', 6: '陸', 7: '柒', 8: '捌', 9: '玖'} 
        chinese_unit = ['仟', '', '拾', '佰'] 
    else: 
        chinese_num = {0: '零', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九'} 
        chinese_unit = ['千', '', '十', '百'] 
    extra_unit = ['', '萬', '億'] 
    num_list = list(str(number)) 
    num_cn = [] 
    zero_num = 0 # 連續0的個數 
    prev_num = '' # 遍歷列表中當前元素的前一位 
    length = len(num_list) 
    for num in num_list: 
        tmp = num 
        if num == '0': # 如果num為0，記錄連續0的數量 
            zero_num += 1 
            num = '' 
        else: 
            zero = '' 
            if zero_num > 0: 
                zero = '零' 
            zero_num = 0 
            # 處理前一位數字為0，後一位為1，並且在十位數上的數值讀法 
            if prev_num in ('0', '') and num == '1' and chinese_unit[length % 4] in ('十', '拾'):
                num = zero + chinese_unit[length % 4] 
            else: 
                num = zero + chinese_num.get(int(num)) + chinese_unit[length % 4] 
        if length % 4 == 1: # 每隔4位加'萬'、'億'拼接 
            if num == '零': 
                num = extra_unit[length // 4] 
            else: 
                num += extra_unit[length // 4] 
        length -= 1 
        num_cn.append(num) 
        prev_num = tmp 
    num_cn = ''.join(num_cn) 
    return num_cn

    # 原文網址：https://kknews.cc/tech/l9aqv99.html
