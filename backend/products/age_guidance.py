"""Age-related nutrient evidence is distinct from a product dosing recommendation."""
ODS='https://ods.od.nih.gov/factsheets/'


def item(title,text,source):
    return dict(title=title,text=text,sourceUrl=source)


def age_guidance(age):
    if age not in ('kids','teens','20s','30s-40s','50s-60s','70-plus'):
        return None
    general='식사로 충족하는 것이 기본입니다. 필요한 영양소라는 사실만으로 보충제가 추가 효과를 주거나 현재 등록 제품의 연령·용량이 적합하다는 뜻은 아닙니다.'
    if age in ('kids','teens'):
        cards=[
            item('비타민 D · 뼈 건강','칼슘 흡수와 뼈 건강에 필요합니다. 성장기 결핍 예방의 근거이지 키 성장 촉진이나 성인용 고함량 제품의 추천 근거는 아닙니다.',ODS+'VITAMIND-Consumer/'),
            item('칼슘 · 뼈·치아 형성','성장기에 뼈와 치아를 만드는 데 필요합니다. 식사 섭취량을 먼저 확인하고 부족 여부에 따라 보충을 검토합니다.',ODS+'Calcium-Consumer/'),
            item('비타민 C · 콜라겐·면역 기능','정상 콜라겐 합성과 면역 기능에 관여합니다. 어린이에게 성인용 500~1000mg 제품이 적합하다는 뜻은 아닙니다.',ODS+'ImmuneFunction-Consumer/'),
            item('프로바이오틱스 · 균주별 검토','모든 유산균이 어린이에게 같은 효과를 내지 않습니다. 사용 목적·균주·안전성·연령별 용량을 확인해야 하며 장기 사용 근거도 제한적입니다.','https://www.nccih.nih.gov/health/tips/things-to-know-about-dietary-supplements-for-children-and-teens')]
        return dict(title='성장기 영양 근거 · 어린이용 제품 추천과 구분',notice=general+' 정확한 만 나이와 제품의 소아용 표시가 필요합니다. 현재 등록 50종 중 해당 확인을 마친 제품은 없습니다.',items=cards,reviewedAt='2026-09-20')
    if age in ('50s-60s','70-plus'):
        cards=[item('비타민 B12 · 50세 이후 흡수','나이가 들면 식품 속 B12 흡수가 줄 수 있어 강화식품·보충제 형태의 B12를 검토할 근거가 있습니다. 고함량 복용이나 기억력 개선을 뜻하지 않습니다.',ODS+'VitaminB12-Consumer/'),
               item('비타민 D·칼슘 · 뼈 건강','뼈 건강과 식사 섭취량을 확인할 영양소입니다. 결핍 여부·질환·복용약을 고려해야 하며 모든 고령자에게 보충제가 골절을 예방한다고 단정할 수 없습니다.',ODS+'Calcium-Consumer/')]
        return dict(title='중·노년기 영양 근거',notice=general+' 아래 그리드는 성인용 표시와 B12 함량이 확인되고 자동 고함량 주의 기준에 걸리지 않은 비교 후보입니다. 제품 복용량은 별도 상담 대상입니다.',items=cards,reviewedAt='2026-09-20')
    return dict(title='성인 영양 근거',notice=general+' 20대·30~40대라는 이유만으로 특정 제품이 더 효과적이라는 근거는 확인되지 않아 성인용 비교 후보로 표시합니다.',items=[
        item('식사·결핍 여부 우선','나이만으로 일률적으로 종합비타민을 권하기보다는 식단과 개인의 필요를 확인해야 합니다.',ODS+'MVMS-Consumer/'),
        item('B12 · 결핍과 활력 구분','B12가 충분한 사람에게 보충제가 에너지나 운동 능력을 추가로 높여준다고 볼 수 없습니다.',ODS+'VitaminB12-Consumer/')],reviewedAt='2026-09-20')
