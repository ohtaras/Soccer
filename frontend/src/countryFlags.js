const COUNTRY_CODES = {
  Albania: 'AL',
  Algeria: 'DZ',
  Argentina: 'AR',
  Armenia: 'AM',
  Australia: 'AU',
  Austria: 'AT',
  Azerbaijan: 'AZ',
  Bangladesh: 'BD',
  Belarus: 'BY',
  Belgium: 'BE',
  Bolivia: 'BO',
  'Bosnia-Herzegovina': 'BA',
  Brazil: 'BR',
  Bulgaria: 'BG',
  Canada: 'CA',
  Chile: 'CL',
  China: 'CN',
  Colombia: 'CO',
  'Costa Rica': 'CR',
  Croatia: 'HR',
  Cyprus: 'CY',
  Czechia: 'CZ',
  Denmark: 'DK',
  Ecuador: 'EC',
  Egypt: 'EG',
  'El Salvador': 'SV',
  Estonia: 'EE',
  'Faroe Islands': 'FO',
  Finland: 'FI',
  France: 'FR',
  Georgia: 'GE',
  Germany: 'DE',
  Ghana: 'GH',
  Greece: 'GR',
  Guatemala: 'GT',
  Honduras: 'HN',
  Hungary: 'HU',
  Iceland: 'IS',
  India: 'IN',
  Indonesia: 'ID',
  Iran: 'IR',
  Iraq: 'IQ',
  Ireland: 'IE',
  Israel: 'IL',
  Italy: 'IT',
  Japan: 'JP',
  Kazakhstan: 'KZ',
  Kuwait: 'KW',
  Latvia: 'LV',
  Lithuania: 'LT',
  Luxembourg: 'LU',
  Malaysia: 'MY',
  Mexico: 'MX',
  Moldova: 'MD',
  Montenegro: 'ME',
  Morocco: 'MA',
  Netherlands: 'NL',
  'New Zealand': 'NZ',
  Nigeria: 'NG',
  'North Macedonia': 'MK',
  Norway: 'NO',
  Panama: 'PA',
  Paraguay: 'PY',
  Peru: 'PE',
  Poland: 'PL',
  Portugal: 'PT',
  Qatar: 'QA',
  Romania: 'RO',
  Russia: 'RU',
  'Saudi Arabia': 'SA',
  Serbia: 'RS',
  Singapore: 'SG',
  Slovakia: 'SK',
  Slovenia: 'SI',
  'South Africa': 'ZA',
  'South Korea': 'KR',
  Spain: 'ES',
  Sweden: 'SE',
  Switzerland: 'CH',
  Tanzania: 'TZ',
  Thailand: 'TH',
  Tunisia: 'TN',
  Turkiye: 'TR',
  Ukraine: 'UA',
  'United Arab Emirates': 'AE',
  'United States': 'US',
  Uruguay: 'UY',
  Uzbekistan: 'UZ',
  Venezuela: 'VE',
  Vietnam: 'VN',
}

// Sub-national UK flags use Unicode tag sequences, not regional indicators.
const SPECIAL_FLAGS = {
  England: '🏴\u{E0067}\u{E0062}\u{E0065}\u{E006E}\u{E0067}\u{E007F}',
  Scotland: '🏴\u{E0067}\u{E0062}\u{E0073}\u{E0063}\u{E0074}\u{E007F}',
  Wales: '🏴\u{E0067}\u{E0062}\u{E0077}\u{E006C}\u{E0073}\u{E007F}',
  'Northern Ireland': '🇬🇧',
}

function codeToFlag(code) {
  return code
    .toUpperCase()
    .split('')
    .map((char) => String.fromCodePoint(0x1f1e6 + char.charCodeAt(0) - 65))
    .join('')
}

export function getCountryFlag(leagueName) {
  if (!leagueName) return null
  const country = leagueName.split(' - ')[0]

  if (SPECIAL_FLAGS[country]) return SPECIAL_FLAGS[country]

  const code = COUNTRY_CODES[country]
  return code ? codeToFlag(code) : null
}
